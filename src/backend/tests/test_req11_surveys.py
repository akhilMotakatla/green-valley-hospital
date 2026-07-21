"""REQ-11 — Patient Satisfaction Survey & Doctor Ratings: automated backend tests.

Acceptance criteria covered (from task brief + requirements §9.11):
  AC-SURV-1  Survey row created for Completed appointment with correct trigger_after
             (now+24h) and expires_at (now+24h+7d); not created for Cancelled/NoShow.
  AC-SURV-2  Poll-on-login fires survey_available notification after trigger_after;
             second login does NOT re-fire.
  AC-SURV-3  Patient submits survey (doctor_rating 1-5, overall_rating 1-5, optional
             comment); duplicate → 409 Conflict.
  AC-SURV-4  Admin calls PATCH remove-comment → comment=null, is_comment_removed=true,
             star ratings unchanged.
  AC-SURV-5  Submission after expires_at → 403 (expired).

Additional acceptance criteria from task brief:
  - Submission before 24h trigger_after window → 400.
  - Survey is immutable after submission (no PATCH endpoint).
  - Doctor sees own aggregate rating (avg, count) and anonymized comments
    (no patient identity exposed).
  - Admin sees full survey with patient identity.
  - Survey prompt expires after 7 days with no submission.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models import (
    Appointment,
    Doctor,
    Notification,
    Patient,
    SatisfactionSurvey,
    User,
)
from app.security import hash_password
from tests.conftest import TEST_MONDAY, auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_appointment(db, patient_id, doctor_id, scheduled_at, status, created_by):
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_at=scheduled_at,
        status=status,
        reason="Test",
        created_by_user_id=created_by,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def _mk_survey(
    db,
    appointment_id,
    patient_id,
    doctor_id,
    trigger_after=None,
    expires_at=None,
    submitted_at=None,
    comment=None,
    doctor_star_rating=None,
    overall_star_rating=None,
    notification_sent=0,
    is_comment_removed=0,
):
    """Insert a SatisfactionSurvey row directly (bypasses HTTP for state setup)."""
    now = datetime.utcnow()
    ta = trigger_after or (now - timedelta(hours=1)).isoformat()  # default: past trigger
    ea = expires_at or (now + timedelta(hours=24 * 7)).isoformat()  # default: not expired

    survey = SatisfactionSurvey(
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        trigger_after=ta,
        expires_at=ea,
        submitted_at=submitted_at,
        doctor_star_rating=doctor_star_rating,
        overall_star_rating=overall_star_rating,
        comment=comment,
        notification_sent=notification_sent,
        is_comment_removed=is_comment_removed,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey


# ---------------------------------------------------------------------------
# AC-SURV-1: Survey row created only for Completed appointments
# ---------------------------------------------------------------------------

def test_survey_created_when_appointment_marked_completed(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """AC-SURV-1: Completing an appointment via doctor status endpoint creates a
    satisfaction_surveys row with correct trigger_after and expires_at.
    """
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )

    resp = client.patch(
        f"/api/doctor/appointments/{appt.appointment_id}/status",
        json={"status": "Completed"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 200, resp.text

    survey = (
        db.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.appointment_id == appt.appointment_id)
        .first()
    )
    assert survey is not None, "No satisfaction_surveys row created for Completed appointment"
    assert survey.submitted_at is None
    assert survey.patient_id == patient_profile.patient_id
    assert survey.doctor_id == doctor_profile.doctor_id

    # trigger_after should be ~24h from now (in the future).
    trigger = datetime.fromisoformat(survey.trigger_after)
    assert trigger > datetime.now(timezone.utc), "trigger_after should be in the future"

    # expires_at should be ~7 days after trigger_after.
    expires = datetime.fromisoformat(survey.expires_at)
    delta = expires - trigger
    assert timedelta(days=6, hours=23) < delta < timedelta(days=7, hours=1), (
        f"expires_at should be 7 days after trigger_after, got delta={delta}"
    )


def test_no_survey_for_cancelled_appointment(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """Survey row must NOT be created when appointment is Cancelled."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    client.patch(
        f"/api/doctor/appointments/{appt.appointment_id}/status",
        json={"status": "Cancelled"},
        headers=auth_headers(doctor_user),
    )

    survey = (
        db.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.appointment_id == appt.appointment_id)
        .first()
    )
    assert survey is None, "Survey should not be created for Cancelled appointment"


def test_no_survey_for_noshow_appointment(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """Survey row must NOT be created when appointment is marked NoShow."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    client.patch(
        f"/api/doctor/appointments/{appt.appointment_id}/status",
        json={"status": "NoShow"},
        headers=auth_headers(doctor_user),
    )

    survey = (
        db.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.appointment_id == appt.appointment_id)
        .first()
    )
    assert survey is None, "Survey should not be created for NoShow appointment"


# ---------------------------------------------------------------------------
# AC-SURV-2: Poll-on-login fires survey_available notification (not twice)
# ---------------------------------------------------------------------------

def test_poll_on_login_fires_survey_notification_after_trigger(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-SURV-2: On first login after trigger_after, survey_available notification
    is created and notification_sent set to 1. Second login does NOT re-fire.
    """
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    # Insert survey with trigger_after already passed.
    survey = _mk_survey(
        db,
        appt.appointment_id,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
        trigger_after=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
        notification_sent=0,
    )

    # First login poll.
    client.get("/api/notifications/unread-count", headers=auth_headers(patient_user))

    notifs = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == patient_user.id,
            Notification.event_type == "survey_available",
        )
        .all()
    )
    assert len(notifs) == 1, f"Expected 1 survey_available notification, got {len(notifs)}"
    db.refresh(survey)
    assert survey.notification_sent == 1

    # Second login poll — notification must NOT be re-fired.
    client.get("/api/notifications/unread-count", headers=auth_headers(patient_user))
    notifs_after = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == patient_user.id,
            Notification.event_type == "survey_available",
        )
        .all()
    )
    assert len(notifs_after) == 1, "survey_available notification fired twice"


# ---------------------------------------------------------------------------
# Survey submission after trigger_after window → 201
# ---------------------------------------------------------------------------

def test_submit_survey_after_trigger_window_succeeds(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-SURV-3 (success path): Patient submits survey; submitted_at is set."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db,
        appt.appointment_id,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
    )  # trigger_after defaults to 1 hour ago → available

    resp = client.post(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={
            "doctor_star_rating": 5,
            "overall_star_rating": 4,
            "comment": "Excellent care",
        },
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["survey_id"] == survey.survey_id
    assert data["submitted_at"] is not None

    db.refresh(survey)
    assert survey.submitted_at is not None
    assert survey.doctor_star_rating == 5
    assert survey.overall_star_rating == 4
    assert survey.comment == "Excellent care"


# ---------------------------------------------------------------------------
# AC-SURV-3: Duplicate submission returns 409
# ---------------------------------------------------------------------------

def test_duplicate_survey_submission_returns_409(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-SURV-3: Submitting the same survey a second time returns 409 Conflict."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id)

    payload = {"doctor_star_rating": 4, "overall_star_rating": 4}
    client.post(f"/api/patients/me/surveys/{survey.survey_id}", json=payload, headers=auth_headers(patient_user))
    resp = client.post(f"/api/patients/me/surveys/{survey.survey_id}", json=payload, headers=auth_headers(patient_user))
    assert resp.status_code == 409
    assert "already been submitted" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Submission before trigger_after window → 400
# ---------------------------------------------------------------------------

def test_submission_before_trigger_window_returns_400(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """Submitting before trigger_after (24h window not yet open) returns 400."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db,
        appt.appointment_id,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
        trigger_after=(datetime.utcnow() + timedelta(hours=23)).isoformat(),  # future
    )

    resp = client.post(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={"doctor_star_rating": 3, "overall_star_rating": 3},
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 400
    assert "not yet available" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# AC-SURV-5: Submission after expires_at → 403
# ---------------------------------------------------------------------------

def test_submission_after_expiry_returns_403(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-SURV-5: Submitting after expires_at returns 403 Forbidden."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db,
        appt.appointment_id,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
        trigger_after=(datetime.utcnow() - timedelta(hours=24 * 8)).isoformat(),
        expires_at=(datetime.utcnow() - timedelta(hours=1)).isoformat(),  # expired
    )

    resp = client.post(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={"doctor_star_rating": 3, "overall_star_rating": 3},
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 403
    assert "expired" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Survey immutability
# ---------------------------------------------------------------------------

def test_survey_immutable_no_patch_endpoint(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """Survey is immutable (SURV-3, SURVFR-3): there is no PATCH endpoint
    for patient survey submission; method not allowed.
    """
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id)

    resp = client.patch(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={"doctor_star_rating": 1},
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 405, (
        f"Expected 405 for PATCH on patient survey, got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Doctor sees aggregate rating + anonymized comments (no patient identity)
# ---------------------------------------------------------------------------

def test_doctor_aggregate_ratings_no_patient_identity(
    client, db, doctor_profile, doctor_user,
    patient_profile, patient_user, patient2_profile, patient2_user
):
    """SURV-5: Doctor sees average rating and count; comment text present but
    NO patient name, patient_id, or any patient-identifying field.
    """
    appt1 = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    appt2 = _mk_appointment(
        db, patient2_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:30:00", "Completed", doctor_user.id
    )

    survey1 = _mk_survey(
        db, appt1.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id,
        doctor_star_rating=5, overall_star_rating=5, comment="Great doctor",
        submitted_at=datetime.utcnow().isoformat()
    )
    survey2 = _mk_survey(
        db, appt2.appointment_id, patient2_profile.patient_id, doctor_profile.doctor_id,
        doctor_star_rating=3, overall_star_rating=4, comment="Good but rushed",
        submitted_at=datetime.utcnow().isoformat()
    )

    resp = client.get("/api/doctor/ratings", headers=auth_headers(doctor_user))
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["total_reviews"] == 2
    assert data["average_doctor_rating"] == 4.0  # (5+3)/2

    # Comments present, no patient identity.
    comments = data["comments"]
    assert len(comments) >= 1
    for c in comments:
        assert "comment" in c
        assert "submitted_at" in c
        # Patient-identifying fields must NOT appear.
        assert "patient_name" not in c
        assert "patient_id" not in c


# ---------------------------------------------------------------------------
# Admin sees full survey with patient identity
# ---------------------------------------------------------------------------

def test_admin_sees_full_survey_with_patient_identity(
    client, db, doctor_profile, doctor_user,
    patient_profile, patient_user, admin_user
):
    """SURV-6: Admin GET /admin/surveys/{id} includes patient_name and patient_id."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id,
        doctor_star_rating=5, overall_star_rating=5, comment="Excellent",
        submitted_at=datetime.utcnow().isoformat()
    )

    resp = client.get(
        f"/api/admin/surveys/{survey.survey_id}",
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["patient_id"] == patient_profile.patient_id
    assert data["patient_name"] is not None
    assert "Patient" in data["patient_name"] or len(data["patient_name"]) > 0
    assert data["comment"] == "Excellent"
    assert data["doctor_star_rating"] == 5


# ---------------------------------------------------------------------------
# AC-SURV-4: Admin moderation — remove comment, star ratings preserved
# ---------------------------------------------------------------------------

def test_admin_remove_comment_star_ratings_preserved(
    client, db, doctor_profile, doctor_user,
    patient_profile, patient_user, admin_user
):
    """AC-SURV-4: PATCH /admin/surveys/{id}/remove-comment nullifies comment and
    sets is_comment_removed=true; star ratings remain intact.
    """
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id,
        doctor_star_rating=4, overall_star_rating=5, comment="Inappropriate comment",
        submitted_at=datetime.utcnow().isoformat()
    )

    resp = client.patch(
        f"/api/admin/surveys/{survey.survey_id}/remove-comment",
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["is_comment_removed"] is True
    assert data["comment"] is None

    # Verify via GET that star ratings are still there.
    get_resp = client.get(
        f"/api/admin/surveys/{survey.survey_id}",
        headers=auth_headers(admin_user),
    )
    get_data = get_resp.json()
    assert get_data["is_comment_removed"] is True
    assert get_data["comment"] is None
    assert get_data["doctor_star_rating"] == 4, "Star rating must not be removed"
    assert get_data["overall_star_rating"] == 5, "Overall star rating must not be removed"


def test_admin_remove_comment_is_idempotent(
    client, db, doctor_profile, doctor_user, patient_profile, admin_user
):
    """PATCH /admin/surveys/{id}/remove-comment is idempotent (SURVFR-5)."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id,
        doctor_star_rating=3, overall_star_rating=3, comment="comment",
        submitted_at=datetime.utcnow().isoformat()
    )

    r1 = client.patch(f"/api/admin/surveys/{survey.survey_id}/remove-comment", headers=auth_headers(admin_user))
    r2 = client.patch(f"/api/admin/surveys/{survey.survey_id}/remove-comment", headers=auth_headers(admin_user))
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["is_comment_removed"] is True


# ---------------------------------------------------------------------------
# Survey star rating validation
# ---------------------------------------------------------------------------

def test_survey_star_rating_out_of_range_rejected(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """doctor_star_rating and overall_star_rating must be integers 1-5."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id)

    # Rating of 0 is invalid.
    resp = client.post(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={"doctor_star_rating": 0, "overall_star_rating": 3},
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 400

    # Rating of 6 is invalid.
    resp = client.post(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={"doctor_star_rating": 6, "overall_star_rating": 3},
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# RBAC: Doctor cannot submit a survey; Patient cannot access admin endpoints
# ---------------------------------------------------------------------------

def test_doctor_cannot_submit_patient_survey(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """Doctor trying to POST to patient survey endpoint returns 403."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id)

    resp = client.post(
        f"/api/patients/me/surveys/{survey.survey_id}",
        json={"doctor_star_rating": 5, "overall_star_rating": 5},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 403


def test_patient_cannot_access_admin_surveys(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """Patient hitting GET /admin/surveys returns 403."""
    resp = client.get("/api/admin/surveys", headers=auth_headers(patient_user))
    assert resp.status_code == 403


def test_patient_cannot_moderate_comments(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """Patient calling PATCH /admin/surveys/{id}/remove-comment returns 403."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    survey = _mk_survey(
        db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id,
        comment="some comment", submitted_at=datetime.utcnow().isoformat()
    )

    resp = client.patch(
        f"/api/admin/surveys/{survey.survey_id}/remove-comment",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Admin list surveys endpoint
# ---------------------------------------------------------------------------

def test_admin_lists_all_surveys_paginated(
    client, db, doctor_profile, doctor_user, patient_profile, admin_user
):
    """Admin GET /admin/surveys returns paginated list with patient and doctor info."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    _mk_survey(
        db, appt.appointment_id, patient_profile.patient_id, doctor_profile.doctor_id,
        doctor_star_rating=4, overall_star_rating=4,
        submitted_at=datetime.utcnow().isoformat()
    )

    resp = client.get("/api/admin/surveys", headers=auth_headers(admin_user))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "patient_name" in item
    assert "doctor_name" in item
    assert "doctor_star_rating" in item
    assert "is_comment_removed" in item
