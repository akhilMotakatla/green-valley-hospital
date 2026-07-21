"""REQ-01 — Doctor Availability & Slot Management: automated backend tests.

Acceptance criteria covered:
  AC-AVL-1  6 slots returned for Mon 09:00-12:00 with 30-min slots, no bookings
  AC-AVL-2  Booked slot (09:30) absent from slot list; 5 slots returned
  AC-AVL-3  Full-day block on the test date returns empty slot list
  AC-AVL-4  Booking an already-taken slot returns 409 Conflict
  AC-AVL-5  No schedule configured for a day returns empty list (not 404/500)

Additional behavioural tests:
  - Doctor can define weekly schedule (POST /api/doctor/availability/schedule)
  - Doctor can set slot duration config (PUT /api/doctor/availability/config)
  - Doctor can create a partial-day block (POST /api/doctor/availability/blocks)
  - Only start_time XOR end_time on a block returns 400
  - Invalid slot_duration_minutes returns 400
  - Admin can view and edit any doctor's schedule / config / blocks (AVLNFR-2)
  - Patient hitting a Doctor-only availability-write endpoint gets 403
"""
from __future__ import annotations

from datetime import datetime

import pytest

from tests.conftest import TEST_MONDAY, auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slot_endpoint(doctor_id: int, date: str) -> str:
    return f"/api/doctors/{doctor_id}/available-slots?date={date}"


def _assert_monday():
    """Sanity: TEST_MONDAY must be a Monday (weekday index 0)."""
    assert datetime.strptime(TEST_MONDAY, "%Y-%m-%d").weekday() == 0, (
        f"TEST_MONDAY ({TEST_MONDAY}) is not a Monday — test setup is wrong"
    )


# ---------------------------------------------------------------------------
# AC-AVL-1: Basic 6-slot response for Mon 09:00-12:00, no bookings
# ---------------------------------------------------------------------------


def test_avl_ac1_six_slots_no_bookings(
    client, db, doctor_profile, monday_schedule, patient_user
):
    """AC-AVL-1: Given Mon 09:00-12:00 with 30-min slots and no appointments,
    GET /api/doctors/{id}/available-slots?date=2026-07-27 returns exactly 6
    slots: 09:00, 09:30, 10:00, 10:30, 11:00, 11:30."""
    _assert_monday()
    headers = auth_headers(patient_user)
    resp = client.get(_slot_endpoint(doctor_profile.doctor_id, TEST_MONDAY), headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["doctor_id"] == doctor_profile.doctor_id
    assert data["date"] == TEST_MONDAY
    assert data["slot_duration_minutes"] == 30
    expected = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"]
    assert data["slots"] == expected, f"Expected {expected}, got {data['slots']}"


# ---------------------------------------------------------------------------
# AC-AVL-2: Booked slot absent; 5 remaining slots
# ---------------------------------------------------------------------------


def test_avl_ac2_booked_slot_absent(
    client, db, doctor_profile, patient_profile, monday_schedule
):
    """AC-AVL-2: An existing Scheduled appointment at 09:30 removes that slot;
    5 slots remain."""
    _assert_monday()
    from app.models import Appointment

    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T09:30:00",
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt)
    db.commit()

    from tests.conftest import auth_headers as _ah

    resp = client.get(
        _slot_endpoint(doctor_profile.doctor_id, TEST_MONDAY),
        headers=_ah(patient_profile.user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "09:30" not in data["slots"], "Booked slot 09:30 should not be available"
    assert len(data["slots"]) == 5
    assert "09:00" in data["slots"]  # adjacent slots still available


# ---------------------------------------------------------------------------
# AC-AVL-3: Full-day block returns empty slot list
# ---------------------------------------------------------------------------


def test_avl_ac3_full_day_block_empty_slots(
    client, db, doctor_profile, patient_user, monday_schedule
):
    """AC-AVL-3: A full-day block (no start/end time) on TEST_MONDAY returns
    an empty slots list."""
    _assert_monday()
    from app.models import DoctorAvailabilityBlock

    block = DoctorAvailabilityBlock(
        doctor_id=doctor_profile.doctor_id,
        block_date=TEST_MONDAY,
        start_time=None,
        end_time=None,
        reason="Conference",
    )
    db.add(block)
    db.commit()

    resp = client.get(
        _slot_endpoint(doctor_profile.doctor_id, TEST_MONDAY),
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200
    assert resp.json()["slots"] == [], "Full-day block must return empty slot list"


# ---------------------------------------------------------------------------
# AC-AVL-4: Booking an unavailable slot returns 409
# ---------------------------------------------------------------------------


def test_avl_ac4_booking_taken_slot_returns_409(
    client, db, doctor_profile, patient_profile, patient2_profile, monday_schedule
):
    """AC-AVL-4: When slot 09:00 is already booked by patient_1, patient_2
    attempting to book the same slot gets 409 Conflict."""
    _assert_monday()
    from app.models import Appointment

    # First booking already exists (direct DB insert simulates prior booking)
    existing = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T09:00:00",
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(existing)
    db.commit()

    # Patient 2 tries to book the same slot via the API
    resp = client.post(
        "/api/patients/me/appointments",
        headers=auth_headers(patient2_profile.user),
        json={
            "doctor_id": doctor_profile.doctor_id,
            "scheduled_at": f"{TEST_MONDAY}T09:00:00",
            "reason": "Check-up",
        },
    )
    assert resp.status_code == 409, (
        f"Expected 409 for an already-booked slot, got {resp.status_code}: {resp.text}"
    )
    detail = resp.json().get("detail", "")
    assert "Slot" in detail or "slot" in detail or "available" in detail.lower(), (
        f"409 detail should mention slot unavailability, got: {detail}"
    )


# ---------------------------------------------------------------------------
# AC-AVL-5: No schedule configured for Wednesday returns empty list
# ---------------------------------------------------------------------------


def test_avl_ac5_no_schedule_returns_empty_list(
    client, db, doctor_profile, patient_user, monday_schedule
):
    """AC-AVL-5: Doctor has no schedule for Wednesday; querying any Wednesday
    returns empty slots — not a 404 or 500."""
    # 2026-07-29 is a Wednesday (Monday 27 + 2)
    wednesday = "2026-07-29"
    assert datetime.strptime(wednesday, "%Y-%m-%d").weekday() == 2

    resp = client.get(
        _slot_endpoint(doctor_profile.doctor_id, wednesday),
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200, (
        f"No schedule should return 200 with empty list, got {resp.status_code}"
    )
    assert resp.json()["slots"] == []


# ---------------------------------------------------------------------------
# Doctor defines weekly availability (POST /api/doctor/availability/schedule)
# ---------------------------------------------------------------------------


def test_avl_doctor_creates_schedule_window(
    client, db, doctor_user, doctor_profile
):
    """REQ-01 AC1: Doctor can create a weekly schedule window via the API."""
    resp = client.post(
        "/api/doctor/availability/schedule",
        headers=auth_headers(doctor_user),
        json={"day_of_week": 1, "start_time": "14:00", "end_time": "17:00"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["doctor_id"] == doctor_profile.doctor_id
    assert data["day_of_week"] == 1
    assert data["start_time"] == "14:00"
    assert data["end_time"] == "17:00"
    assert data["is_active"] is True


def test_avl_doctor_gets_own_schedule(
    client, db, doctor_user, doctor_profile, monday_schedule
):
    """Doctor can retrieve their weekly schedule."""
    resp = client.get(
        "/api/doctor/availability/schedule",
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["day_of_week"] == 0
    assert items[0]["start_time"] == "09:00"


def test_avl_schedule_invalid_day_of_week_returns_400(
    client, db, doctor_user, doctor_profile
):
    """day_of_week must be 0–6; 7 returns 400."""
    resp = client.post(
        "/api/doctor/availability/schedule",
        headers=auth_headers(doctor_user),
        json={"day_of_week": 7, "start_time": "09:00", "end_time": "12:00"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Doctor sets slot duration config (AVLFR-2 valid values)
# ---------------------------------------------------------------------------


def test_avl_doctor_sets_slot_duration(
    client, db, doctor_user, doctor_profile
):
    """Doctor can configure slot duration to a valid value (30 → 15 min)."""
    resp = client.put(
        "/api/doctor/availability/config",
        headers=auth_headers(doctor_user),
        json={"slot_duration_minutes": 15},
    )
    assert resp.status_code == 200
    assert resp.json()["slot_duration_minutes"] == 15


def test_avl_invalid_slot_duration_returns_400(
    client, db, doctor_user, doctor_profile
):
    """AVLFR-2: Slot duration not in {10,15,20,30,45,60} → 400."""
    resp = client.put(
        "/api/doctor/availability/config",
        headers=auth_headers(doctor_user),
        json={"slot_duration_minutes": 25},
    )
    assert resp.status_code == 400


def test_avl_slot_duration_reflected_in_slot_response(
    client, db, doctor_user, doctor_profile, patient_user, monday_schedule
):
    """When slot_duration_minutes = 60, Mon 09:00-12:00 yields 3 slots not 6."""
    _assert_monday()
    # Set duration to 60 minutes
    r = client.put(
        "/api/doctor/availability/config",
        headers=auth_headers(doctor_user),
        json={"slot_duration_minutes": 60},
    )
    assert r.status_code == 200

    resp = client.get(
        _slot_endpoint(doctor_profile.doctor_id, TEST_MONDAY),
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["slot_duration_minutes"] == 60
    assert len(data["slots"]) == 3
    assert data["slots"] == ["09:00", "10:00", "11:00"]


# ---------------------------------------------------------------------------
# Doctor creates a date-specific block
# ---------------------------------------------------------------------------


def test_avl_doctor_creates_full_day_block(
    client, db, doctor_user, doctor_profile
):
    """REQ-01 AC2: Doctor creates a full-day block (no start/end time)."""
    resp = client.post(
        "/api/doctor/availability/blocks",
        headers=auth_headers(doctor_user),
        json={"block_date": TEST_MONDAY, "reason": "Conference"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["block_date"] == TEST_MONDAY
    assert data["start_time"] is None
    assert data["end_time"] is None


def test_avl_doctor_creates_partial_day_block(
    client, db, doctor_user, doctor_profile
):
    """Doctor creates a time-range block (start_time + end_time both present)."""
    resp = client.post(
        "/api/doctor/availability/blocks",
        headers=auth_headers(doctor_user),
        json={"block_date": TEST_MONDAY, "start_time": "10:00", "end_time": "12:00"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "12:00"


def test_avl_partial_block_only_removes_blocked_hours(
    client, db, doctor_user, doctor_profile, patient_user, monday_schedule
):
    """A 10:00-12:00 partial block leaves 09:00, 09:30 available."""
    _assert_monday()
    # Create partial block via API
    r = client.post(
        "/api/doctor/availability/blocks",
        headers=auth_headers(doctor_user),
        json={"block_date": TEST_MONDAY, "start_time": "10:00", "end_time": "12:00"},
    )
    assert r.status_code == 201

    resp = client.get(
        _slot_endpoint(doctor_profile.doctor_id, TEST_MONDAY),
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200
    slots = resp.json()["slots"]
    assert "09:00" in slots
    assert "09:30" in slots
    assert "10:00" not in slots
    assert "10:30" not in slots
    assert "11:00" not in slots
    assert "11:30" not in slots


def test_avl_block_missing_end_time_returns_400(
    client, db, doctor_user, doctor_profile
):
    """AVLFR-3: Only one of start_time/end_time → 400."""
    resp = client.post(
        "/api/doctor/availability/blocks",
        headers=auth_headers(doctor_user),
        json={"block_date": TEST_MONDAY, "start_time": "10:00"},
    )
    assert resp.status_code == 400


def test_avl_block_missing_start_time_returns_400(
    client, db, doctor_user, doctor_profile
):
    """AVLFR-3: Only end_time without start_time → 400."""
    resp = client.post(
        "/api/doctor/availability/blocks",
        headers=auth_headers(doctor_user),
        json={"block_date": TEST_MONDAY, "end_time": "12:00"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Admin can view and edit any doctor's availability (AVLNFR-2, AC7)
# ---------------------------------------------------------------------------


def test_avl_admin_views_doctor_schedule(
    client, db, admin_user, doctor_profile, monday_schedule
):
    """REQ-01 AC7: Admin can GET any doctor's schedule."""
    resp = client.get(
        f"/api/admin/doctors/{doctor_profile.doctor_id}/availability/schedule",
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["day_of_week"] == 0


def test_avl_admin_creates_schedule_window(
    client, db, admin_user, doctor_profile
):
    """Admin can create a schedule window for any doctor."""
    resp = client.post(
        f"/api/admin/doctors/{doctor_profile.doctor_id}/availability/schedule",
        headers=auth_headers(admin_user),
        json={"day_of_week": 2, "start_time": "09:00", "end_time": "13:00"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["doctor_id"] == doctor_profile.doctor_id
    assert data["day_of_week"] == 2


def test_avl_admin_updates_slot_config(
    client, db, admin_user, doctor_profile
):
    """Admin can change any doctor's slot_duration_minutes."""
    resp = client.put(
        f"/api/admin/doctors/{doctor_profile.doctor_id}/availability/config",
        headers=auth_headers(admin_user),
        json={"slot_duration_minutes": 20},
    )
    assert resp.status_code == 200
    assert resp.json()["slot_duration_minutes"] == 20


def test_avl_admin_creates_block_for_doctor(
    client, db, admin_user, doctor_profile
):
    """Admin can create an availability block for any doctor."""
    resp = client.post(
        f"/api/admin/doctors/{doctor_profile.doctor_id}/availability/blocks",
        headers=auth_headers(admin_user),
        json={"block_date": TEST_MONDAY, "reason": "Admin override"},
    )
    assert resp.status_code == 201
    assert resp.json()["doctor_id"] == doctor_profile.doctor_id


# ---------------------------------------------------------------------------
# RBAC: Patient cannot write to Doctor/Admin availability-write endpoints
# ---------------------------------------------------------------------------


def test_avl_patient_cannot_write_doctor_schedule(
    client, db, patient_user, patient_profile, doctor_profile
):
    """AVLNFR-2: Patient calling a Doctor-write endpoint gets 403."""
    resp = client.post(
        "/api/doctor/availability/schedule",
        headers=auth_headers(patient_user),
        json={"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
    )
    assert resp.status_code == 403


def test_avl_patient_cannot_write_admin_schedule(
    client, db, patient_user, patient_profile, doctor_profile
):
    """AVLNFR-2: Patient calling an Admin-write availability endpoint gets 403."""
    resp = client.post(
        f"/api/admin/doctors/{doctor_profile.doctor_id}/availability/schedule",
        headers=auth_headers(patient_user),
        json={"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# RBAC: Unauthenticated request to slot endpoint → 403
# ---------------------------------------------------------------------------


def test_avl_unauthenticated_slots_request_returns_403(
    client, db, doctor_profile, monday_schedule
):
    """Available-slots endpoint requires authentication."""
    resp = client.get(_slot_endpoint(doctor_profile.doctor_id, TEST_MONDAY))
    # FastAPI's HTTPBearer returns 403 when no Authorization header supplied
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Missing or invalid date query param → 400
# ---------------------------------------------------------------------------


def test_avl_invalid_date_format_returns_400(
    client, db, doctor_profile, patient_user
):
    """date must be YYYY-MM-DD; passing garbage returns 400."""
    resp = client.get(
        f"/api/doctors/{doctor_profile.doctor_id}/available-slots?date=not-a-date",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 400
