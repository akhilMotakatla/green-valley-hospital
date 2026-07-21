"""REQ-04 — Vitals Trend Visualization: automated backend tests.

Acceptance criteria covered (from requirements §9.4 and task brief):
  1. Staff records vitals for a patient → 201 (AC-VIT-1)
  2. Doctor attempts to record vitals → 403 (VIT-5)
  3. Patient attempts to record vitals → 403 (VIT-5)
  4. BP requires both systolic and diastolic — systolic alone → 400 (AC-VIT-2, VITFR-2)
  5. GET /patients/{id}/vitals — doctor can read own patient's vitals → 200
  6. GET /patients/{id}/vitals — doctor cannot read another doctor's patient → 403 (AC-VIT-4, VITFR-6)
  7. Vitals returned sorted ascending by recorded_at (VITFR-4)
"""
from __future__ import annotations

import pytest

from app.models import Appointment, Department, Doctor, Patient, User, Vitals
from app.security import hash_password
from app.utils import now_iso
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_appointment(db, patient_id: int, doctor_id: int, user_id: int) -> Appointment:
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_at="2026-08-01T09:00:00",
        status="Scheduled",
        created_by_user_id=user_id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


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

class TestREQ04Vitals:

    def test_staff_records_vitals_returns_201(
        self, client, db, staff_user, staff_member, patient_user, patient_profile
    ):
        """Criterion 1: Staff records vitals for a patient → 201 (AC-VIT-1)."""
        resp = client.post(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            json={
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "weight_kg": 70.5,
                "pulse_bpm": 72,
                "temperature_celsius": 36.8,
            },
            headers=auth_headers(staff_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["systolic_bp"] == 120
        assert data["diastolic_bp"] == 80
        assert data["weight_kg"] == 70.5
        assert data["pulse_bpm"] == 72
        assert data["temperature_celsius"] == 36.8
        assert data["recorded_by_user_id"] == staff_user.id
        assert data["patient_id"] == patient_profile.patient_id

    def test_doctor_cannot_record_vitals_returns_403(
        self, client, db, doctor_user, doctor_profile, patient_user, patient_profile
    ):
        """Criterion 2: Doctor attempts to record vitals → 403 (VIT-5)."""
        resp = client.post(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            json={"pulse_bpm": 72},
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 403

    def test_patient_cannot_record_vitals_returns_403(
        self, client, db, patient_user, patient_profile
    ):
        """Criterion 3: Patient attempts to record vitals → 403 (VIT-5)."""
        resp = client.post(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            json={"pulse_bpm": 72},
            headers=auth_headers(patient_user),
        )
        assert resp.status_code == 403

    def test_bp_requires_both_systolic_and_diastolic(
        self, client, db, staff_user, staff_member, patient_user, patient_profile
    ):
        """Criterion 4: systolic_bp provided without diastolic_bp → 400 (AC-VIT-2, VITFR-2)."""
        resp = client.post(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            json={"systolic_bp": 120},
            headers=auth_headers(staff_user),
        )
        assert resp.status_code == 400

    def test_doctor_reads_own_patients_vitals(
        self, client, db, doctor_user, doctor_profile, staff_user, staff_member,
        patient_user, patient_profile
    ):
        """Criterion 5: Doctor can read own patient's vitals (AUTHZ-2, VITFR-6)."""
        # Create appointment to establish doctor-patient relationship
        _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)

        # Record vitals as staff
        client.post(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            json={"pulse_bpm": 80},
            headers=auth_headers(staff_user),
        )

        resp = client.get(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["pulse_bpm"] == 80

    def test_doctor_cannot_read_another_doctors_patients_vitals(
        self, client, db, doctor_user, doctor_profile, patient_user, patient_profile, dept
    ):
        """Criterion 6: Doctor cannot read another doctor's patient vitals → 403 (AC-VIT-4)."""
        # Create a second doctor — no appointment relationship with patient_profile
        doctor2_user, _ = _make_second_doctor(db, dept)

        resp = client.get(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            headers=auth_headers(doctor2_user),
        )
        assert resp.status_code == 403

    def test_vitals_returned_sorted_ascending_by_recorded_at(
        self, client, db, doctor_user, doctor_profile, staff_user, staff_member,
        patient_user, patient_profile
    ):
        """Criterion 7: Vitals returned sorted ascending by recorded_at (VITFR-4)."""
        # Establish doctor-patient relationship
        _make_appointment(db, patient_profile.patient_id, doctor_profile.doctor_id, patient_user.id)

        # Insert two vitals records with explicit recorded_at in reverse order
        v1 = Vitals(
            patient_id=patient_profile.patient_id,
            recorded_by_user_id=staff_user.id,
            pulse_bpm=60,
            recorded_at="2026-06-01T08:00:00",
        )
        v2 = Vitals(
            patient_id=patient_profile.patient_id,
            recorded_by_user_id=staff_user.id,
            pulse_bpm=80,
            recorded_at="2026-07-01T09:00:00",
        )
        db.add(v2)
        db.add(v1)
        db.commit()

        resp = client.get(
            f"/api/patients/{patient_profile.patient_id}/vitals",
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2
        # Ascending order: earlier recorded_at first
        assert items[0]["recorded_at"] < items[1]["recorded_at"]
        assert items[0]["pulse_bpm"] == 60
        assert items[1]["pulse_bpm"] == 80
