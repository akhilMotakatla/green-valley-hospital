"""REQ-05 — Inter-Department Referral Management: automated backend tests.

Acceptance criteria covered (from requirements §9.5 and task brief):
  1. Doctor creates referral for own patient → 201, status=Pending (AC-REF-1)
  2. Doctor creates referral for another doctor's patient → 403 (REFFR-5)
  3. Receiving doctor accepts referral → status=Accepted, notifications created (AC-REF-2)
  4. Receiving doctor declines with note → status=Declined, notifications created
  5. Accepting an already-Accepted referral → 409 (AC-REF-4)
  6. Accepting a Declined referral → 409
  7. Completing a Pending referral directly → 409 (REFFR-1)
  8. Patient sees own referrals: status visible, reason excluded (AC-REF-5, REFNFR-1)

Setup: two departments (Cardiology, Neurology), two doctors, one patient.
Doctor A (Cardiology) has an appointment with the patient and creates referrals to Neurology.
Doctor B (Neurology) accepts or declines.
"""
from __future__ import annotations

import pytest

from app.models import (
    Appointment,
    Department,
    Doctor,
    Notification,
    Patient,
    Referral,
    User,
)
from app.security import hash_password
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dept(db, name: str) -> Department:
    d = Department(name=name, description=f"{name} care", is_active=1)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _make_doctor(db, dept_id: int, email: str, full_name: str) -> tuple[User, Doctor]:
    u = User(
        email=email,
        password_hash=hash_password("Pass1234"),
        role="Doctor",
        full_name=full_name,
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    d = Doctor(user_id=u.id, department_id=dept_id, specialty="General", years_experience=5)
    db.add(d)
    db.commit()
    db.refresh(d)
    return u, d


def _make_appointment(db, patient_id: int, doctor_id: int, user_id: int, scheduled_at: str = "2026-08-01T09:00:00") -> Appointment:
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_at=scheduled_at,
        status="Scheduled",
        created_by_user_id=user_id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def _create_referral(client, doctor_user: User, patient_id: int, to_department_id: int, urgency: str = "Routine") -> dict:
    resp = client.post(
        "/api/doctor/referrals",
        json={
            "patient_id": patient_id,
            "to_department_id": to_department_id,
            "reason": "Clinical evaluation needed",
            "urgency": urgency,
        },
        headers=auth_headers(doctor_user),
    )
    return resp


# ---------------------------------------------------------------------------
# Fixture: full referral setup
# ---------------------------------------------------------------------------

@pytest.fixture()
def referral_setup(db, client, patient_user, patient_profile):
    """Two departments, two doctors. Doctor A has appointment with patient."""
    dept_a = _make_dept(db, "Cardiology")
    dept_b = _make_dept(db, "Neurology")

    doctor_a_user, doctor_a = _make_doctor(db, dept_a.department_id, "doctor_a@hospital.test", "Dr. Alpha")
    doctor_b_user, doctor_b = _make_doctor(db, dept_b.department_id, "doctor_b@hospital.test", "Dr. Beta")

    # Doctor A has appointment with the patient → AUTHZ-2 satisfied
    _make_appointment(db, patient_profile.patient_id, doctor_a.doctor_id, doctor_a_user.id)

    return {
        "dept_a": dept_a,
        "dept_b": dept_b,
        "doctor_a_user": doctor_a_user,
        "doctor_a": doctor_a,
        "doctor_b_user": doctor_b_user,
        "doctor_b": doctor_b,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestREQ05Referrals:

    def test_doctor_creates_referral_for_own_patient_201_pending(
        self, client, db, patient_profile, referral_setup
    ):
        """Criterion 1: Doctor creates referral for own patient → 201, status=Pending (AC-REF-1)."""
        s = referral_setup
        resp = _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "Pending"
        assert data["referring_doctor_id"] == s["doctor_a"].doctor_id
        assert data["receiving_department_id"] == s["dept_b"].department_id
        assert data["patient_id"] == patient_profile.patient_id

    def test_doctor_creates_referral_for_another_doctors_patient_returns_403(
        self, client, db, patient_profile, referral_setup
    ):
        """Criterion 2: Doctor creates referral for a patient with no appointment → 403 (REFFR-5)."""
        s = referral_setup
        # Doctor B has NO appointment with the patient — AUTHZ-2 should reject
        resp = _create_referral(client, s["doctor_b_user"], patient_profile.patient_id, s["dept_a"].department_id)
        assert resp.status_code == 403

    def test_receiving_doctor_accepts_referral(
        self, client, db, patient_user, patient_profile, referral_setup
    ):
        """Criterion 3: Receiving doctor accepts referral → status=Accepted, notifications created (AC-REF-2)."""
        s = referral_setup

        # Doctor A creates referral to dept_b
        create_resp = _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)
        assert create_resp.status_code == 201
        referral_id = create_resp.json()["referral_id"]

        # Doctor B accepts
        accept_resp = client.patch(
            f"/api/doctor/referrals/{referral_id}/accept",
            json={"note": "Happy to take this patient"},
            headers=auth_headers(s["doctor_b_user"]),
        )
        assert accept_resp.status_code == 200
        data = accept_resp.json()
        assert data["status"] == "Accepted"
        assert data["receiving_doctor_id"] == s["doctor_b"].doctor_id

        # Notifications should have been created for patient and referring doctor
        notifs = db.query(Notification).filter(
            Notification.event_type == "referral_status_changed"
        ).all()
        recipient_ids = {n.recipient_user_id for n in notifs}
        # Patient and doctor_a should both be notified
        assert patient_user.id in recipient_ids
        assert s["doctor_a_user"].id in recipient_ids

    def test_receiving_doctor_declines_with_note(
        self, client, db, patient_user, patient_profile, referral_setup
    ):
        """Criterion 4: Receiving doctor declines with note → status=Declined, notifications created."""
        s = referral_setup

        create_resp = _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)
        assert create_resp.status_code == 201
        referral_id = create_resp.json()["referral_id"]

        decline_resp = client.patch(
            f"/api/doctor/referrals/{referral_id}/decline",
            json={"note": "Capacity full this month"},
            headers=auth_headers(s["doctor_b_user"]),
        )
        assert decline_resp.status_code == 200
        data = decline_resp.json()
        assert data["status"] == "Declined"
        assert data["receiving_doctor_note"] == "Capacity full this month"

        # Both patient and referring doctor should be notified
        notifs = db.query(Notification).filter(
            Notification.event_type == "referral_status_changed"
        ).all()
        recipient_ids = {n.recipient_user_id for n in notifs}
        assert patient_user.id in recipient_ids
        assert s["doctor_a_user"].id in recipient_ids

    def test_accepting_already_accepted_referral_returns_409(
        self, client, db, patient_profile, referral_setup
    ):
        """Criterion 5: Accepting an already-Accepted referral → 409 (AC-REF-4)."""
        s = referral_setup

        create_resp = _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)
        referral_id = create_resp.json()["referral_id"]

        # First accept succeeds
        client.patch(
            f"/api/doctor/referrals/{referral_id}/accept",
            json={},
            headers=auth_headers(s["doctor_b_user"]),
        )

        # Second accept should return 409
        second_accept = client.patch(
            f"/api/doctor/referrals/{referral_id}/accept",
            json={},
            headers=auth_headers(s["doctor_b_user"]),
        )
        assert second_accept.status_code == 409

    def test_accepting_declined_referral_returns_409(
        self, client, db, patient_profile, referral_setup
    ):
        """Criterion 6: Accepting a Declined referral → 409."""
        s = referral_setup

        create_resp = _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)
        referral_id = create_resp.json()["referral_id"]

        # Decline the referral first
        client.patch(
            f"/api/doctor/referrals/{referral_id}/decline",
            json={"note": "No capacity"},
            headers=auth_headers(s["doctor_b_user"]),
        )

        # Now try to accept the declined referral → 409
        accept_resp = client.patch(
            f"/api/doctor/referrals/{referral_id}/accept",
            json={},
            headers=auth_headers(s["doctor_b_user"]),
        )
        assert accept_resp.status_code == 409

    def test_completing_pending_referral_directly_returns_409(
        self, client, db, patient_profile, referral_setup
    ):
        """Criterion 7: Completing a Pending referral directly → 409 (REFFR-1 lifecycle)."""
        s = referral_setup

        create_resp = _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)
        referral_id = create_resp.json()["referral_id"]

        # The referral is still Pending — set receiving_doctor_id so AUTHZ check passes
        # We need to manually set receiving_doctor_id since complete checks that
        referral = db.get(Referral, referral_id)
        referral.receiving_doctor_id = s["doctor_b"].doctor_id
        db.commit()

        # Try to complete a Pending referral — should be 409
        complete_resp = client.patch(
            f"/api/doctor/referrals/{referral_id}/complete",
            headers=auth_headers(s["doctor_b_user"]),
        )
        assert complete_resp.status_code == 409

    def test_patient_sees_own_referrals_reason_excluded(
        self, client, db, patient_user, patient_profile, referral_setup
    ):
        """Criterion 8: Patient sees own referrals, status visible, reason excluded (AC-REF-5)."""
        s = referral_setup

        _create_referral(client, s["doctor_a_user"], patient_profile.patient_id, s["dept_b"].department_id)

        resp = client.get(
            "/api/patients/me/referrals",
            headers=auth_headers(patient_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        referral = data["items"][0]
        # Status must be visible
        assert "status" in referral
        assert referral["status"] == "Pending"
        # Reason must NOT be in patient-facing response
        assert "reason" not in referral
