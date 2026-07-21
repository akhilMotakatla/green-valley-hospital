"""REQ-03 — Patient Pre-Visit Intake Form: automated backend tests.

Acceptance criteria covered (from requirements §9.3 and task brief):
  1. Patient submits intake form for own Scheduled appointment → 200 (PATCH)
  2. Second submission replaces first (upsert) → 200, single row in DB
  3. Submission after appointment is Completed → 403 (spec: INTAKEFR-4, AC-INTAKE-2)
  4. Another patient submitting for someone else's appointment → 403 (INTAKEFR-5)
  5. Doctor reads intake for their own patient's appointment → 200 (INTAKE-4)
  6. Doctor reads intake for another doctor's patient → 403 (INTAKEFR-5)
  7. GET intake for appointment with no submission → {submitted: false} (INTAKE-4)

Note: AC-INTAKE-2 / INTAKEFR-4 both specify 403 for the Completed-appointment
guard; the task brief listed 400, but 403 is the authoritative requirement text
and what the implementation returns.
"""
from __future__ import annotations

import pytest

from app.models import Appointment, Department, Doctor, IntakeForm, Patient, User
from app.security import hash_password
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_appointment(db, patient_id: int, doctor_id: int, user_id: int, status: str = "Scheduled") -> Appointment:
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_at="2026-08-01T09:00:00",
        status=status,
        created_by_user_id=user_id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def _make_intake(db, appointment_id: int, patient_id: int) -> IntakeForm:
    form = IntakeForm(appointment_id=appointment_id, patient_id=patient_id)
    db.add(form)
    db.commit()
    db.refresh(form)
    return form


def _make_second_doctor(db, dept: Department) -> tuple[User, Doctor]:
    u = User(
        email="dr.second@hospital.test",
        password_hash=hash_password("Pass1234"),
        role="Doctor",
        full_name="Dr. Second",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    d = Doctor(user_id=u.id, department_id=dept.department_id, specialty="Cardiology", years_experience=3)
    db.add(d)
    db.commit()
    db.refresh(d)
    return u, d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestREQ03Intake:

    def test_patient_submits_own_scheduled_appointment(
        self, client, db, patient_user, patient_profile, doctor_user, doctor_profile
    ):
        """Criterion 1: Patient submits intake form for own Scheduled appointment → 200."""
        appt = _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)
        _make_intake(db, appt.appointment_id, patient_profile.patient_id)

        resp = client.patch(
            f"/api/appointments/{appt.appointment_id}/intake",
            json={
                "chief_complaint": "Chest tightness",
                "symptom_duration": "3 days",
                "pain_scale": 7,
                "submit": True,
            },
            headers=auth_headers(patient_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["submitted"] is True
        assert data["submitted_at"] is not None
        assert data["pain_scale"] == 7
        assert data["chief_complaint"] == "Chest tightness"

    def test_second_submission_upserts_single_row(
        self, client, db, patient_user, patient_profile, doctor_user, doctor_profile
    ):
        """Criterion 2: Second submission replaces first — still 200, only one DB row."""
        appt = _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)
        _make_intake(db, appt.appointment_id, patient_profile.patient_id)

        client.patch(
            f"/api/appointments/{appt.appointment_id}/intake",
            json={"chief_complaint": "First complaint", "symptom_duration": "1 day", "pain_scale": 3, "submit": True},
            headers=auth_headers(patient_user),
        )

        resp = client.patch(
            f"/api/appointments/{appt.appointment_id}/intake",
            json={"chief_complaint": "Updated complaint", "symptom_duration": "2 days", "pain_scale": 5, "submit": True},
            headers=auth_headers(patient_user),
        )
        assert resp.status_code == 200
        assert resp.json()["chief_complaint"] == "Updated complaint"

        count = db.query(IntakeForm).filter(IntakeForm.appointment_id == appt.appointment_id).count()
        assert count == 1

    def test_submission_after_completed_returns_403(
        self, client, db, patient_user, patient_profile, doctor_user, doctor_profile
    ):
        """Criterion 3: Submission after appointment is Completed → 403 (AC-INTAKE-2, INTAKEFR-4)."""
        appt = _make_appointment(
            db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id, status="Completed"
        )
        _make_intake(db, appt.appointment_id, patient_profile.patient_id)

        resp = client.patch(
            f"/api/appointments/{appt.appointment_id}/intake",
            json={"chief_complaint": "Attempt after complete", "symptom_duration": "3 days", "submit": True},
            headers=auth_headers(patient_user),
        )
        assert resp.status_code == 403

    def test_other_patient_submits_for_someone_elses_appointment_returns_403(
        self, client, db, patient_user, patient_profile, patient2_user, patient2_profile,
        doctor_user, doctor_profile
    ):
        """Criterion 4: Patient B submitting for Patient A's appointment → 403 (INTAKEFR-5)."""
        appt = _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)
        _make_intake(db, appt.appointment_id, patient_profile.patient_id)

        resp = client.patch(
            f"/api/appointments/{appt.appointment_id}/intake",
            json={"chief_complaint": "Not my appointment", "symptom_duration": "1 day", "submit": True},
            headers=auth_headers(patient2_user),
        )
        assert resp.status_code == 403

    def test_doctor_reads_own_patients_intake_returns_200(
        self, client, db, doctor_user, doctor_profile, patient_user, patient_profile
    ):
        """Criterion 5: Doctor reads intake for their own patient's appointment → 200 (INTAKE-4)."""
        appt = _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)
        _make_intake(db, appt.appointment_id, patient_profile.patient_id)

        # Submit intake as patient first
        client.patch(
            f"/api/appointments/{appt.appointment_id}/intake",
            json={"chief_complaint": "Headache", "symptom_duration": "1 day", "submit": True},
            headers=auth_headers(patient_user),
        )

        resp = client.get(
            f"/api/appointments/{appt.appointment_id}/intake",
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 200
        assert resp.json()["submitted"] is True

    def test_doctor_reads_another_doctors_patient_intake_returns_403(
        self, client, db, doctor_user, doctor_profile, patient_user, patient_profile, dept
    ):
        """Criterion 6: Doctor reads intake for another doctor's patient → 403 (INTAKEFR-5)."""
        # Create a second doctor in the same department
        doctor2_user, doctor2_profile = _make_second_doctor(db, dept)

        # Appointment is assigned to doctor_profile (not doctor2_profile)
        appt = _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)
        _make_intake(db, appt.appointment_id, patient_profile.patient_id)

        # doctor2 tries to GET — should be 403
        resp = client.get(
            f"/api/appointments/{appt.appointment_id}/intake",
            headers=auth_headers(doctor2_user),
        )
        assert resp.status_code == 403

    def test_get_intake_no_submission_returns_submitted_false(
        self, client, db, doctor_user, doctor_profile, patient_user, patient_profile
    ):
        """Criterion 7: GET intake for appointment with no intake form row → {submitted: false}."""
        appt = _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)
        # Intentionally NOT creating an IntakeForm row

        resp = client.get(
            f"/api/appointments/{appt.appointment_id}/intake",
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 200
        assert resp.json()["submitted"] is False
