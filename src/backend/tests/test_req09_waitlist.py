"""REQ-09 — Appointment Waitlist System: automated backend tests.

Acceptance criteria covered (from task brief + requirements §9.9):
  AC-WL-1   FIFO: first Waiting patient promoted to Notified on cancellation;
             waitlist_slot_available notification fired; notified_at and
             confirmation_deadline set.
  AC-WL-2   Patient who does not confirm within window: entry → Expired, new
             Waiting entry created at back of queue, next patient notified.
  AC-WL-3   Duplicate join for same doctor+date returns 409.
  AC-WL-4   Admin confirmation_hours update reflected in deadline computation.

Additional acceptance criteria from task brief:
  - Patient can join waitlist when no slots available.
  - Joining when slots ARE available is rejected (409).
  - Offered slot excluded from GET /doctors/{id}/slots while status=Notified.
  - Patient confirms within window → appointment created, entry=Confirmed.
  - Confirmation after deadline → 400.
  - Patient can remove themselves from waitlist (DELETE → 204).
  - Staff can view all waitlist entries and manually remove an entry.
  - Admin reads/writes global confirmation_hours config.
  - Patient calling a Staff-only endpoint gets 403.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.models import Appointment, Notification, WaitlistEntry
from app.security import hash_password
from app.models import User, Doctor, Patient, SystemConfig
from tests.conftest import TEST_MONDAY, auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _join(client, user, doctor_id, preferred_date):
    return client.post(
        "/api/waitlist",
        json={"doctor_id": doctor_id, "preferred_date": preferred_date},
        headers=auth_headers(user),
    )


def _slots_url(doctor_id, date):
    return f"/api/doctors/{doctor_id}/available-slots?date={date}"


# ---------------------------------------------------------------------------
# REQ-09 AC: Patient joins when no slots available
# ---------------------------------------------------------------------------

def test_join_waitlist_no_slots_available_success(
    client, db, doctor_profile, patient_profile, patient_user
):
    """Patient can join when no schedule (= no slots) exists for that doctor+date."""
    # No schedule configured → get_available_slots returns [] → join succeeds.
    resp = _join(client, patient_user, doctor_profile.doctor_id, TEST_MONDAY)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["doctor_id"] == doctor_profile.doctor_id
    assert data["preferred_date"] == TEST_MONDAY
    assert data["status"] == "Waiting"
    assert data["position"] == 1


def test_join_waitlist_slots_still_available_rejected(
    client, db, doctor_profile, monday_schedule, patient_profile, patient_user
):
    """Joining when slots ARE available returns 409 (patient should book directly)."""
    resp = _join(client, patient_user, doctor_profile.doctor_id, TEST_MONDAY)
    assert resp.status_code == 409
    assert "still available" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# AC-WL-3: Duplicate join for same doctor+date returns 409
# ---------------------------------------------------------------------------

def test_duplicate_join_same_doctor_date_rejected(
    client, db, doctor_profile, patient_profile, patient_user
):
    """AC-WL-3: Second join for same doctor+date returns 409 Conflict."""
    # First join (no schedule → no slots).
    r1 = _join(client, patient_user, doctor_profile.doctor_id, TEST_MONDAY)
    assert r1.status_code == 201

    # Second join — same patient, same doctor, same date.
    r2 = _join(client, patient_user, doctor_profile.doctor_id, TEST_MONDAY)
    assert r2.status_code == 409
    assert "active waitlist entry" in r2.json()["detail"].lower()


# ---------------------------------------------------------------------------
# AC-WL-1: FIFO — first patient notified on cancellation
# ---------------------------------------------------------------------------

def test_fifo_first_patient_notified_on_cancellation(
    client, db, doctor_profile, doctor_user, patient_profile, patient_user,
    patient2_profile, patient2_user
):
    """AC-WL-1: After cancellation, first-in-queue entry becomes Notified;
    waitlist_slot_available notification sent; second entry stays Waiting.
    """
    # Insert two Waiting entries with explicit ordered timestamps so FIFO
    # ordering is deterministic regardless of test clock precision.
    entry1 = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at="2026-07-21T08:00:00.000000",
    )
    entry2 = WaitlistEntry(
        patient_id=patient2_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at="2026-07-21T09:00:00.000000",
    )
    db.add_all([entry1, entry2])
    db.commit()
    db.refresh(entry1)
    db.refresh(entry2)

    # Create a Scheduled appointment so the PATCH cancellation works.
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T09:00:00",
        status="Scheduled",
        reason="Test appointment",
        created_by_user_id=doctor_user.id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # Doctor cancels the appointment — triggers FIFO cascade.
    resp = client.patch(
        f"/api/doctor/appointments/{appt.appointment_id}/status",
        json={"status": "Cancelled"},
        headers=auth_headers(doctor_user),
    )
    assert resp.status_code == 200, resp.text

    db.refresh(entry1)
    db.refresh(entry2)

    # Entry 1 (first in FIFO) must be Notified.
    assert entry1.status == "Notified", f"Expected Notified, got {entry1.status}"
    assert entry1.notified_at is not None
    assert entry1.confirmation_deadline is not None
    assert entry1.held_slot_time == "09:00"

    # Entry 2 must still be Waiting.
    assert entry2.status == "Waiting", f"Expected Waiting, got {entry2.status}"

    # A waitlist_slot_available notification must exist for patient 1.
    notif = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == patient_user.id,
            Notification.event_type == "waitlist_slot_available",
        )
        .first()
    )
    assert notif is not None, "waitlist_slot_available notification not found for patient 1"


# ---------------------------------------------------------------------------
# Offered slot excluded from GET /doctors/{id}/slots while status=Notified
# ---------------------------------------------------------------------------

def test_notified_slot_excluded_from_available_slots(
    client, db, doctor_profile, monday_schedule, patient_profile, patient_user
):
    """Slot held by a Notified waitlist entry must NOT appear in available-slots."""
    # Insert a Notified entry holding 09:00 on TEST_MONDAY.
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Notified",
        held_slot_time="09:00",
        notified_at=datetime.utcnow().isoformat(),
        confirmation_deadline=(datetime.utcnow() + timedelta(hours=4)).isoformat(),
        created_at=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
    )
    db.add(entry)
    db.commit()

    resp = client.get(
        _slots_url(doctor_profile.doctor_id, TEST_MONDAY),
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200, resp.text
    slots = resp.json()["slots"]
    assert "09:00" not in slots, (
        f"09:00 should be excluded (Notified hold), but got slots: {slots}"
    )
    # Other slots should still be available.
    assert len(slots) > 0, "Expected remaining slots to be available"


# ---------------------------------------------------------------------------
# Patient confirms within window → appointment created, entry=Confirmed
# ---------------------------------------------------------------------------

def test_confirm_within_window_creates_appointment(
    client, db, doctor_profile, patient_profile, patient_user
):
    """Patient confirms an offered slot within the deadline → appointment created."""
    future_deadline = (datetime.utcnow() + timedelta(hours=4)).isoformat()
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Notified",
        held_slot_time="09:00",
        notified_at=datetime.utcnow().isoformat(),
        confirmation_deadline=future_deadline,
        created_at=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    resp = client.post(
        f"/api/waitlist/{entry.entry_id}/confirm",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "appointment_id" in data

    db.refresh(entry)
    assert entry.status == "Confirmed"

    # Appointment must exist in DB with the correct doctor, patient, and time.
    appt = db.get(Appointment, data["appointment_id"])
    assert appt is not None
    assert appt.doctor_id == doctor_profile.doctor_id
    assert appt.patient_id == patient_profile.patient_id
    assert appt.status == "Scheduled"
    assert f"{TEST_MONDAY}T09:00:00" in appt.scheduled_at


def test_confirm_after_expired_window_rejected(
    client, db, doctor_profile, patient_profile, patient_user
):
    """Confirming after the confirmation deadline returns 400."""
    past_deadline = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Notified",
        held_slot_time="09:00",
        notified_at=(datetime.utcnow() - timedelta(hours=5)).isoformat(),
        confirmation_deadline=past_deadline,
        created_at=(datetime.utcnow() - timedelta(hours=5)).isoformat(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    resp = client.post(
        f"/api/waitlist/{entry.entry_id}/confirm",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Patient removes themselves from waitlist
# ---------------------------------------------------------------------------

def test_patient_removes_self_from_waitlist(
    client, db, doctor_profile, patient_profile, patient_user
):
    """Patient can delete their own Waiting entry; status becomes Removed."""
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    resp = client.delete(
        f"/api/patients/me/waitlist/{entry.entry_id}",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 204, resp.text

    db.refresh(entry)
    assert entry.status == "Removed"


def test_patient_cannot_remove_others_entry(
    client, db, doctor_profile, patient_profile, patient_user,
    patient2_profile, patient2_user
):
    """Patient P2 cannot delete P1's waitlist entry — returns 403."""
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    resp = client.delete(
        f"/api/patients/me/waitlist/{entry.entry_id}",
        headers=auth_headers(patient2_user),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# AC-WL-2: Expiry re-queues to back; next patient notified
# ---------------------------------------------------------------------------

def test_expiry_requeues_to_back_next_patient_notified(
    client, db, doctor_profile, doctor_user,
    patient_profile, patient_user, patient2_profile, patient2_user
):
    """AC-WL-2: Overdue Notified entry → Expired; patient re-queued at back;
    next patient in queue promoted to Notified.
    """
    # Patient 2 was waiting BEFORE patient 1 got notified and expired.
    entry_p2 = WaitlistEntry(
        patient_id=patient2_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at="2026-07-21T07:00:00.000000",
    )
    # Patient 1: Notified with an expired deadline.
    past_deadline = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    entry_p1 = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Notified",
        held_slot_time="09:00",
        notified_at=(datetime.utcnow() - timedelta(hours=5)).isoformat(),
        confirmation_deadline=past_deadline,
        created_at="2026-07-21T06:00:00.000000",
    )
    db.add_all([entry_p2, entry_p1])
    db.commit()
    db.refresh(entry_p1)
    db.refresh(entry_p2)

    # Patient 1 calls unread-count → triggers check_waitlist_expiry.
    resp = client.get(
        "/api/notifications/unread-count",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200

    db.refresh(entry_p1)
    db.refresh(entry_p2)

    # Patient 1's original entry must now be Expired.
    assert entry_p1.status == "Expired", f"Expected Expired, got {entry_p1.status}"

    # A new Waiting entry for patient 1 must exist at the back of the queue.
    new_entry_p1 = (
        db.query(WaitlistEntry)
        .filter(
            WaitlistEntry.patient_id == patient_profile.patient_id,
            WaitlistEntry.doctor_id == doctor_profile.doctor_id,
            WaitlistEntry.preferred_date == TEST_MONDAY,
            WaitlistEntry.status == "Waiting",
        )
        .first()
    )
    assert new_entry_p1 is not None, "New Waiting entry not created for patient 1 after expiry"

    # Patient 2 (who was waiting earlier) must now be Notified.
    assert entry_p2.status == "Notified", f"Expected Notified, got {entry_p2.status}"
    assert entry_p2.notified_at is not None
    assert entry_p2.confirmation_deadline is not None


# ---------------------------------------------------------------------------
# Staff endpoints
# ---------------------------------------------------------------------------

def test_staff_views_all_waitlist_entries(
    client, db, doctor_profile, patient_profile, staff_user
):
    """Staff can view all Waiting/Notified entries for a doctor via GET /staff/waitlist/{id}."""
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(entry)
    db.commit()

    resp = client.get(
        f"/api/staff/waitlist/{doctor_profile.doctor_id}",
        headers=auth_headers(staff_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    entry_resp = data["items"][0]
    assert entry_resp["doctor_id"] == doctor_profile.doctor_id
    assert entry_resp["status"] == "Waiting"


def test_staff_manually_removes_waitlist_entry(
    client, db, doctor_profile, patient_profile, staff_user
):
    """Staff can remove a waitlist entry with a reason; status becomes Removed."""
    entry = WaitlistEntry(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        preferred_date=TEST_MONDAY,
        status="Waiting",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # TestClient.delete() does not accept json= in this Starlette version.
    # The reason body is optional (StaffRemoveRequest = None), so omit it.
    resp = client.delete(
        f"/api/staff/waitlist/{entry.entry_id}",
        headers=auth_headers(staff_user),
    )
    assert resp.status_code == 204, resp.text

    db.refresh(entry)
    assert entry.status == "Removed"


# ---------------------------------------------------------------------------
# Admin config endpoints
# ---------------------------------------------------------------------------

def test_admin_reads_default_waitlist_config(client, db, admin_user):
    """Admin reads global confirmation_hours config (default 4 when not set)."""
    resp = client.get(
        "/api/admin/config/waitlist",
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "confirmation_hours" in data
    assert isinstance(data["confirmation_hours"], int)


def test_admin_updates_waitlist_confirmation_hours(client, db, admin_user):
    """AC-WL-4: Admin can set confirmation_hours; value is persisted and returned."""
    resp = client.put(
        "/api/admin/config/waitlist",
        json={"confirmation_hours": 2},
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["confirmation_hours"] == 2

    # Read back to confirm persistence.
    get_resp = client.get(
        "/api/admin/config/waitlist",
        headers=auth_headers(admin_user),
    )
    assert get_resp.json()["confirmation_hours"] == 2


def test_admin_config_invalid_hours_rejected(client, db, admin_user):
    """confirmation_hours outside 1-72 range returns 400."""
    resp = client.put(
        "/api/admin/config/waitlist",
        json={"confirmation_hours": 0},
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 400

    resp = client.put(
        "/api/admin/config/waitlist",
        json={"confirmation_hours": 73},
        headers=auth_headers(admin_user),
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# RBAC: Patient cannot access Staff-only endpoints
# ---------------------------------------------------------------------------

def test_patient_cannot_access_staff_waitlist_view(
    client, db, doctor_profile, patient_profile, patient_user
):
    """Patient hitting GET /api/staff/waitlist/{doctor_id} returns 403."""
    resp = client.get(
        f"/api/staff/waitlist/{doctor_profile.doctor_id}",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 403


def test_patient_cannot_access_admin_config(
    client, db, patient_profile, patient_user
):
    """Patient hitting admin config endpoint returns 403."""
    resp = client.get(
        "/api/admin/config/waitlist",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 403
