"""REQ-10 — Discharge Summary & Follow-Up Scheduling: automated backend tests.

Acceptance criteria covered (from task brief + requirements §9.10):
  AC-DS-1   Doctor submits discharge for a Scheduled appointment → appointment
            atomically becomes Completed, discharge row created, notification sent,
            patient can read the summary.
  AC-DS-2   Submitting discharge for a non-Scheduled appointment (Cancelled,
            NoShow, already-Completed) → 400 Bad Request.
  AC-DS-3   Follow-up appointment created atomically with discharge summary;
            both rows visible.
  AC-DS-4   Patient P calling GET on appointment belonging to Patient Q → 403.

Additional acceptance criteria from task brief:
  - Follow-up for an already-taken slot → 409, entire transaction rolled back
    (no discharge summary created, appointment still Scheduled).
  - Non-assigned doctor cannot submit discharge → 403.
  - Discharge summary is read-only (no PATCH endpoint exists).
  - Duplicate discharge summary creation → 400 (status check fires first).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models import (
    Appointment,
    DischargeSummary,
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

def _discharge_url(appointment_id: int) -> str:
    return f"/api/doctor/appointments/{appointment_id}/discharge-summary"


def _mk_appointment(db, patient_id, doctor_id, scheduled_at, status, created_by):
    """Create and commit a bare Appointment directly in DB."""
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


# ---------------------------------------------------------------------------
# AC-DS-1: Discharge for Scheduled → appointment becomes Completed atomically
# ---------------------------------------------------------------------------

def test_discharge_scheduled_appointment_becomes_completed(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-DS-1(a): Discharge submitted for Scheduled appt → appointment Completed,
    discharge_summaries row created.
    """
    appt = _mk_appointment(
        db,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00",
        "Scheduled",
        doctor_user.id,
    )

    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Mild hypertension noted"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["key_findings"] == "Mild hypertension noted"
    assert data["appointment_id"] == appt.appointment_id
    assert data["doctor_id"] == doctor_profile.doctor_id
    assert data["patient_id"] == patient_profile.patient_id

    # Appointment must now be Completed (atomic status transition).
    db.refresh(appt)
    assert appt.status == "Completed", f"Expected Completed, got {appt.status}"

    # Discharge summary row must exist.
    summary = (
        db.query(DischargeSummary)
        .filter(DischargeSummary.appointment_id == appt.appointment_id)
        .first()
    )
    assert summary is not None
    assert summary.key_findings == "Mild hypertension noted"


def test_discharge_creates_discharge_summary_ready_notification(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-DS-1(b): discharge_summary_ready notification created for patient."""
    appt = _mk_appointment(
        db,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00",
        "Scheduled",
        doctor_user.id,
    )

    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "All clear"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 201, resp.text

    notif = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == patient_user.id,
            Notification.event_type == "discharge_summary_ready",
        )
        .first()
    )
    assert notif is not None, "discharge_summary_ready notification not found for patient"


def test_patient_can_read_own_discharge_summary(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user
):
    """AC-DS-1(c): Patient retrieves discharge summary via
    GET /patients/me/appointments/{id}/discharge-summary.
    """
    appt = _mk_appointment(
        db,
        patient_profile.patient_id,
        doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00",
        "Scheduled",
        doctor_user.id,
    )
    # Create discharge via API.
    client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Stable vitals"},
        headers=auth_headers(doctor_user),
    )

    resp = client.get(
        f"/api/patients/me/appointments/{appt.appointment_id}/discharge-summary",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["key_findings"] == "Stable vitals"


# ---------------------------------------------------------------------------
# AC-DS-2: Non-Scheduled appointment returns 400
# ---------------------------------------------------------------------------

def test_discharge_for_cancelled_appointment_rejected(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """AC-DS-2: Discharge for Cancelled appointment → 400 Bad Request."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Cancelled", doctor_user.id
    )
    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Should fail"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 400, resp.text


def test_discharge_for_noshow_appointment_rejected(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """AC-DS-2: Discharge for NoShow appointment → 400 Bad Request."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "NoShow", doctor_user.id
    )
    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Should fail"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 400, resp.text


def test_discharge_for_already_completed_appointment_rejected(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """Discharge for an already-Completed appointment (without a summary) → 400.
    The status guard fires before the idempotency guard.
    """
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Completed", doctor_user.id
    )
    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Should fail"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 400, resp.text


# ---------------------------------------------------------------------------
# AC-DS-3: Follow-up appointment created atomically with discharge
# ---------------------------------------------------------------------------

def test_follow_up_created_atomically_with_discharge(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user,
    monday_schedule
):
    """AC-DS-3: When follow_up block is provided, both discharge summary and
    follow-up appointment rows are created in a single commit.
    """
    # Original appointment occupies 09:00; follow-up targets 09:30 (available).
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )

    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={
            "key_findings": "Good recovery expected",
            "follow_up": {"scheduled_at": f"{TEST_MONDAY}T09:30:00"},
        },
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["follow_up_appointment_id"] is not None

    fu_appt = db.get(Appointment, data["follow_up_appointment_id"])
    assert fu_appt is not None
    assert fu_appt.status == "Scheduled"
    assert fu_appt.patient_id == patient_profile.patient_id
    assert fu_appt.doctor_id == doctor_profile.doctor_id
    assert "09:30" in fu_appt.scheduled_at


# ---------------------------------------------------------------------------
# Follow-up for taken slot → 409, entire transaction rolled back
# ---------------------------------------------------------------------------

def test_follow_up_taken_slot_returns_409_and_rolls_back(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user,
    monday_schedule
):
    """If follow-up slot is already taken, the whole request returns 409 and
    NO discharge summary is created (atomic rollback per OI-8).
    """
    # Original appointment at 09:00.
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    # Another appointment already occupying 09:30 (the desired follow-up slot).
    _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:30:00", "Scheduled", doctor_user.id
    )

    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={
            "key_findings": "Should fail atomically",
            "follow_up": {"scheduled_at": f"{TEST_MONDAY}T09:30:00"},
        },
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 409, resp.text

    # Discharge summary must NOT have been created (transaction rolled back).
    summary = (
        db.query(DischargeSummary)
        .filter(DischargeSummary.appointment_id == appt.appointment_id)
        .first()
    )
    assert summary is None, "Discharge summary should not exist after 409 rollback"

    # Appointment must still be Scheduled (not Completed).
    db.refresh(appt)
    assert appt.status == "Scheduled", (
        f"Appointment should still be Scheduled after rollback, got {appt.status}"
    )


# ---------------------------------------------------------------------------
# Non-assigned doctor cannot submit discharge → 403
# ---------------------------------------------------------------------------

def test_non_assigned_doctor_cannot_submit_discharge(
    client, db, doctor_profile, doctor_user, patient_profile, dept
):
    """Non-assigned doctor calling POST /discharge-summary returns 403."""
    # Create a second doctor with their own user.
    other_user = User(
        email="dr.other@hospital.test",
        password_hash=hash_password("Pass1234"),
        role="Doctor",
        full_name="Dr. Other",
        is_active=1,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    other_doctor = Doctor(
        user_id=other_user.id,
        department_id=dept.department_id,
        specialty="Neurology",
        years_experience=5,
    )
    db.add(other_doctor)
    db.commit()

    # Appointment belongs to the first doctor.
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )

    # Second doctor tries to submit discharge for first doctor's appointment.
    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Should be forbidden"},
        headers=auth_headers(other_user),
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# AC-DS-4: Patient P cannot read Patient Q's discharge summary
# ---------------------------------------------------------------------------

def test_patient_cannot_read_others_discharge_summary(
    client, db, doctor_profile, doctor_user,
    patient_profile, patient_user, patient2_profile, patient2_user
):
    """AC-DS-4: GET discharge-summary for another patient's appointment → 403."""
    # Appointment and discharge for patient 1.
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Patient 1 findings"},
        headers=auth_headers(doctor_user),
    )

    # Patient 2 tries to read patient 1's discharge summary.
    resp = client.get(
        f"/api/patients/me/appointments/{appt.appointment_id}/discharge-summary",
        headers=auth_headers(patient2_user),
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Discharge summary is read-only (no PATCH endpoint)
# ---------------------------------------------------------------------------

def test_no_patch_endpoint_for_discharge_summary(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """Discharge summaries are immutable (DSFR-8): PATCH returns 405."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Original findings"},
        headers=auth_headers(doctor_user),
    )

    resp = client.patch(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Attempted edit"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 405, (
        f"Expected 405 Method Not Allowed for PATCH on discharge-summary, got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Discharge also creates a satisfaction survey row (REQ-11 integration)
# ---------------------------------------------------------------------------

def test_discharge_creates_satisfaction_survey_row(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """Submitting a discharge summary creates a satisfaction_surveys row
    (create_survey_for_appointment called after appointment set to Completed).
    """
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    resp = client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Survey should be created"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 201, resp.text

    survey = (
        db.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.appointment_id == appt.appointment_id)
        .first()
    )
    assert survey is not None, "SatisfactionSurvey row not created after discharge"
    assert survey.submitted_at is None
    assert survey.patient_id == patient_profile.patient_id
    assert survey.doctor_id == doctor_profile.doctor_id
    # trigger_after must be set ~24h in the future.
    trigger = datetime.fromisoformat(survey.trigger_after)
    assert trigger > datetime.now(timezone.utc), "trigger_after should be in the future"


# ---------------------------------------------------------------------------
# Doctor can read their own discharge summary
# ---------------------------------------------------------------------------

def test_doctor_reads_own_discharge_summary(
    client, db, doctor_profile, doctor_user, patient_profile
):
    """GET /api/doctor/appointments/{id}/discharge-summary returns the summary."""
    appt = _mk_appointment(
        db, patient_profile.patient_id, doctor_profile.doctor_id,
        f"{TEST_MONDAY}T09:00:00", "Scheduled", doctor_user.id
    )
    client.post(
        _discharge_url(appt.appointment_id),
        json={"key_findings": "Doctor view findings"},
        headers=auth_headers(doctor_user),
    )

    resp = client.get(
        _discharge_url(appt.appointment_id),
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["key_findings"] == "Doctor view findings"
