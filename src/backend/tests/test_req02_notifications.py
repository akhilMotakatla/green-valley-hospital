"""REQ-02 — In-App Notification Center: automated backend tests.

Acceptance criteria covered:
  AC-NOTIF-1  appointment_confirmed for patient + doctor on booking
  AC-NOTIF-2  unread-count updates after mark-all-read
  AC-NOTIF-3  GET /notifications scoped to caller only (cross-user isolation)
  AC-NOTIF-4  lab_result_ready for patient + ordering doctor (no other users)
  AC-NOTIF-5  contact_form_received to all active Admin + Staff (no doctors/patients)

Additional behavioural tests:
  - appointment_cancelled → patient + doctor both notified
  - appointment_noshow → patient notified only
  - invoice_created → patient notified
  - contact_form_received goes to admin user AND staff user
  - GET /notifications returns paginated, newest-first, owner-scoped items
  - PATCH /notifications/{id}/read marks single notification read; 403 on others
  - POST /notifications/mark-all-read bulk-marks and returns count
  - Deferred appointment_reminder fires for both patient AND doctor via
    check_and_fire_deferred_notifications (Issue 4 regression)
  - Deferred reminder does NOT fire for a different patient's schedule
    (Issue 1 regression — cross-patient data leak fix)
  - NotificationSchedule is_fired=1 only AFTER both patient AND doctor
    notifications are created
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.models import (
    Appointment,
    Doctor,
    Invoice,
    LabOrder,
    LabResult,
    Notification,
    NotificationSchedule,
    Patient,
    User,
)
from app.services.notification_service import check_and_fire_deferred_notifications
from tests.conftest import TEST_MONDAY, auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_notifications(db, recipient_user_id: int, event_type: str) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == recipient_user_id,
            Notification.event_type == event_type,
        )
        .count()
    )


def _past_iso(hours_ago: int = 25) -> str:
    return (datetime.utcnow() - timedelta(hours=hours_ago)).isoformat()


def _future_iso(hours_ahead: int = 25) -> str:
    return (datetime.utcnow() + timedelta(hours=hours_ahead)).isoformat()


# ---------------------------------------------------------------------------
# AC-NOTIF-1: appointment_confirmed → patient + doctor both notified
# ---------------------------------------------------------------------------


def test_notif_ac1_appointment_confirmed_patient_and_doctor(
    client, db, doctor_profile, patient_profile, monday_schedule
):
    """AC-NOTIF-1: When a Patient books an appointment, both the patient and
    doctor receive an 'appointment_confirmed' notification row."""
    doctor_user_id = doctor_profile.user_id
    patient_user_id = patient_profile.user_id

    resp = client.post(
        "/api/patients/me/appointments",
        headers=auth_headers(patient_profile.user),
        json={
            "doctor_id": doctor_profile.doctor_id,
            "scheduled_at": f"{TEST_MONDAY}T09:00:00",
            "reason": "Annual check-up",
        },
    )
    assert resp.status_code == 201, resp.text

    patient_notifs = _count_notifications(db, patient_user_id, "appointment_confirmed")
    doctor_notifs = _count_notifications(db, doctor_user_id, "appointment_confirmed")

    assert patient_notifs == 1, (
        f"Expected 1 appointment_confirmed for patient, got {patient_notifs}"
    )
    assert doctor_notifs == 1, (
        f"Expected 1 appointment_confirmed for doctor, got {doctor_notifs}"
    )


# ---------------------------------------------------------------------------
# appointment_cancelled → patient + doctor both notified
# ---------------------------------------------------------------------------


def test_notif_appointment_cancelled_patient_and_doctor(
    client, db, doctor_user, doctor_profile, patient_profile
):
    """When a Doctor cancels an appointment, both patient and doctor receive
    'appointment_cancelled'."""
    # Create an appointment directly in the DB (skip slot checks)
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T09:00:00",
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    resp = client.patch(
        f"/api/doctor/appointments/{appt.appointment_id}/status",
        headers=auth_headers(doctor_user),
        json={"status": "Cancelled"},
    )
    assert resp.status_code == 200, resp.text

    patient_cancel = _count_notifications(
        db, patient_profile.user_id, "appointment_cancelled"
    )
    doctor_cancel = _count_notifications(
        db, doctor_user.id, "appointment_cancelled"
    )
    assert patient_cancel == 1, (
        f"Expected 1 appointment_cancelled for patient, got {patient_cancel}"
    )
    assert doctor_cancel == 1, (
        f"Expected 1 appointment_cancelled for doctor, got {doctor_cancel}"
    )


def test_notif_appointment_cancelled_via_staff(
    client, db, staff_user, staff_member, doctor_profile, patient_profile
):
    """Staff cancelling an appointment also notifies patient and doctor."""
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T10:00:00",
        status="Scheduled",
        created_by_user_id=staff_user.id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    resp = client.patch(
        f"/api/staff/appointments/{appt.appointment_id}",
        headers=auth_headers(staff_user),
        json={"status": "Cancelled"},
    )
    assert resp.status_code == 200, resp.text

    assert _count_notifications(db, patient_profile.user_id, "appointment_cancelled") == 1
    assert _count_notifications(db, doctor_profile.user_id, "appointment_cancelled") == 1


# ---------------------------------------------------------------------------
# appointment_noshow → patient notified only
# ---------------------------------------------------------------------------


def test_notif_appointment_noshow_patient_only(
    client, db, doctor_user, doctor_profile, patient_profile
):
    """NoShow transition notifies patient but not doctor (per spec table)."""
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T09:00:00",
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    resp = client.patch(
        f"/api/doctor/appointments/{appt.appointment_id}/status",
        headers=auth_headers(doctor_user),
        json={"status": "NoShow"},
    )
    assert resp.status_code == 200, resp.text

    patient_noshow = _count_notifications(db, patient_profile.user_id, "appointment_noshow")
    doctor_noshow = _count_notifications(db, doctor_user.id, "appointment_noshow")
    assert patient_noshow == 1, (
        f"Expected 1 appointment_noshow for patient, got {patient_noshow}"
    )
    assert doctor_noshow == 0, (
        f"Doctor should NOT receive appointment_noshow, got {doctor_noshow}"
    )


def test_notif_appointment_noshow_via_staff(
    client, db, staff_user, staff_member, doctor_profile, patient_profile
):
    """Staff marking NoShow also notifies the patient (not doctor)."""
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=f"{TEST_MONDAY}T10:00:00",
        status="Scheduled",
        created_by_user_id=staff_user.id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    resp = client.patch(
        f"/api/staff/appointments/{appt.appointment_id}",
        headers=auth_headers(staff_user),
        json={"status": "NoShow"},
    )
    assert resp.status_code == 200, resp.text

    assert _count_notifications(db, patient_profile.user_id, "appointment_noshow") == 1
    assert _count_notifications(db, doctor_profile.user_id, "appointment_noshow") == 0


# ---------------------------------------------------------------------------
# AC-NOTIF-4: lab_result_ready → patient + ordering doctor only
# ---------------------------------------------------------------------------


def test_notif_ac4_lab_result_ready_patient_and_doctor(
    client, db, lab_user, lab_tech, doctor_profile, patient_profile, admin_user
):
    """AC-NOTIF-4: Marking a lab result completed notifies the ordering doctor
    and the patient — not admin or other unrelated users."""
    # Create a lab order for the patient ordered by this doctor
    order = LabOrder(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        test_type="Lab",
        status="Pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Lab submits the result
    resp = client.post(
        f"/api/lab/orders/{order.order_id}/results",
        headers=auth_headers(lab_user),
        data={"result_data": "Normal results"},
    )
    assert resp.status_code == 201, resp.text

    patient_ready = _count_notifications(db, patient_profile.user_id, "lab_result_ready")
    doctor_ready = _count_notifications(db, doctor_profile.user_id, "lab_result_ready")
    admin_ready = _count_notifications(db, admin_user.id, "lab_result_ready")

    assert patient_ready == 1, (
        f"Expected 1 lab_result_ready for patient, got {patient_ready}"
    )
    assert doctor_ready == 1, (
        f"Expected 1 lab_result_ready for ordering doctor, got {doctor_ready}"
    )
    assert admin_ready == 0, (
        f"Admin should NOT receive lab_result_ready, got {admin_ready}"
    )


# ---------------------------------------------------------------------------
# invoice_created → patient notified
# ---------------------------------------------------------------------------


def test_notif_invoice_created_patient_notified(
    client, db, patient_profile, admin_user
):
    """Creating a billing invoice notifies the patient with 'invoice_created'."""
    from app.models import BillingSpecialist

    # Create a BillingSpecialist user
    bill_user = User(
        email="billing@hospital.test",
        password_hash="x",
        role="BillingSpecialist",
        full_name="Billing Spec",
        is_active=1,
    )
    db.add(bill_user)
    db.commit()
    db.refresh(bill_user)

    bs = BillingSpecialist(user_id=bill_user.id)
    db.add(bs)
    db.commit()

    resp = client.post(
        "/api/billing/invoices",
        headers=auth_headers(bill_user),
        json={
            "patient_id": patient_profile.patient_id,
            "line_items": [
                {"description": "Consultation", "amount_cents": 10000}
            ],
            "total_amount_cents": 10000,
        },
    )
    assert resp.status_code == 201, resp.text

    inv_notifs = _count_notifications(db, patient_profile.user_id, "invoice_created")
    assert inv_notifs == 1, (
        f"Expected 1 invoice_created notification for patient, got {inv_notifs}"
    )


# ---------------------------------------------------------------------------
# AC-NOTIF-5: contact_form_received → all active Admin + Staff users
# ---------------------------------------------------------------------------


def test_notif_ac5_contact_form_received_admin_and_staff_only(
    client, db, admin_user, staff_user, staff_member, doctor_user, doctor_profile, patient_user, patient_profile
):
    """AC-NOTIF-5: Submitting the public contact form notifies every active
    Admin and Staff user; Doctors and Patients do NOT receive the notification."""
    resp = client.post(
        "/api/public/contact-messages",
        json={
            "name": "John Visitor",
            "email": "john@example.com",
            "subject": "Inquiry",
            "message": "Hello there",
        },
    )
    assert resp.status_code == 201, resp.text

    admin_cfr = _count_notifications(db, admin_user.id, "contact_form_received")
    staff_cfr = _count_notifications(db, staff_user.id, "contact_form_received")
    doctor_cfr = _count_notifications(db, doctor_user.id, "contact_form_received")
    patient_cfr = _count_notifications(db, patient_user.id, "contact_form_received")

    assert admin_cfr == 1, (
        f"Admin should receive contact_form_received, got {admin_cfr}"
    )
    assert staff_cfr == 1, (
        f"Staff should receive contact_form_received, got {staff_cfr}"
    )
    assert doctor_cfr == 0, (
        f"Doctor should NOT receive contact_form_received, got {doctor_cfr}"
    )
    assert patient_cfr == 0, (
        f"Patient should NOT receive contact_form_received, got {patient_cfr}"
    )


# ---------------------------------------------------------------------------
# AC-NOTIF-2 / AC-NOTIF-3: GET /notifications scoped to caller; unread count
# ---------------------------------------------------------------------------


def test_notif_ac3_isolation_patient_b_cannot_see_patient_a_notifications(
    client, db, patient_profile, patient2_profile, doctor_profile
):
    """AC-NOTIF-3: Patient B's GET /notifications does not include Patient A's
    notifications."""
    from app.services.notification_service import create_notifications

    # Create a notification for patient A directly
    create_notifications(db, [{
        "recipient_user_id": patient_profile.user_id,
        "event_type": "appointment_confirmed",
        "title": "A's appt",
        "body": "Patient A only",
        "related_entity_type": None,
        "related_entity_id": None,
    }])
    db.commit()

    # Patient B queries their notifications
    resp = client.get(
        "/api/notifications",
        headers=auth_headers(patient2_profile.user),
    )
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    # None of the items should belong to patient A
    for item in items:
        # We can't check recipient_user_id from the response (it's not returned),
        # but the total count for patient B should be 0
        pass
    assert data["total"] == 0, (
        f"Patient B should see 0 notifications, got {data['total']}"
    )


def test_notif_ac2_unread_count_and_mark_all_read(
    client, db, doctor_user, doctor_profile, patient_profile
):
    """AC-NOTIF-2: Doctor has 3 unread notifications; unread-count returns 3;
    after mark-all-read it returns 0."""
    from app.services.notification_service import create_notifications

    for i in range(3):
        create_notifications(db, [{
            "recipient_user_id": doctor_user.id,
            "event_type": "appointment_confirmed",
            "title": f"Notification {i}",
            "body": "test",
            "related_entity_type": None,
            "related_entity_id": None,
        }])
    db.commit()

    # Check unread count
    resp = client.get("/api/notifications/unread-count", headers=auth_headers(doctor_user))
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 3

    # Mark all read
    resp2 = client.post("/api/notifications/mark-all-read", headers=auth_headers(doctor_user))
    assert resp2.status_code == 200
    assert resp2.json()["marked_read"] == 3

    # Unread count should now be 0
    resp3 = client.get("/api/notifications/unread-count", headers=auth_headers(doctor_user))
    assert resp3.status_code == 200
    assert resp3.json()["unread_count"] == 0


def test_notif_get_notifications_pagination(
    client, db, patient_user, patient_profile
):
    """GET /notifications returns paginated results for the calling user."""
    from app.services.notification_service import create_notifications

    for i in range(5):
        create_notifications(db, [{
            "recipient_user_id": patient_user.id,
            "event_type": "appointment_confirmed",
            "title": f"Notif {i}",
            "body": "body",
            "related_entity_type": None,
            "related_entity_id": None,
        }])
    db.commit()

    resp = client.get(
        "/api/notifications?page=1&page_size=3",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total_pages"] == 2


# ---------------------------------------------------------------------------
# PATCH /notifications/{id}/read
# ---------------------------------------------------------------------------


def test_notif_mark_one_read(client, db, patient_user, patient_profile):
    """PATCH /notifications/{id}/read sets is_read=True for the caller's notification."""
    from app.services.notification_service import create_notifications

    create_notifications(db, [{
        "recipient_user_id": patient_user.id,
        "event_type": "invoice_created",
        "title": "Invoice",
        "body": "body",
        "related_entity_type": None,
        "related_entity_id": None,
    }])
    db.commit()

    notif = (
        db.query(Notification)
        .filter(Notification.recipient_user_id == patient_user.id)
        .first()
    )
    assert notif is not None
    assert notif.is_read == 0

    resp = client.patch(
        f"/api/notifications/{notif.notification_id}/read",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_read"] is True
    assert data["notification_id"] == notif.notification_id

    db.refresh(notif)
    assert notif.is_read == 1


def test_notif_mark_other_users_notification_read_returns_403(
    client, db, patient_user, patient_profile, patient2_user, patient2_profile
):
    """Attempting to mark another user's notification as read returns 403."""
    from app.services.notification_service import create_notifications

    # Create notification for patient 1
    create_notifications(db, [{
        "recipient_user_id": patient_user.id,
        "event_type": "invoice_created",
        "title": "Invoice",
        "body": "body",
        "related_entity_type": None,
        "related_entity_id": None,
    }])
    db.commit()

    notif = (
        db.query(Notification)
        .filter(Notification.recipient_user_id == patient_user.id)
        .first()
    )

    # Patient 2 tries to mark patient 1's notification as read
    resp = client.patch(
        f"/api/notifications/{notif.notification_id}/read",
        headers=auth_headers(patient2_user),
    )
    assert resp.status_code == 403, (
        f"Expected 403 when marking another user's notification, got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Deferred appointment_reminder — direct service call (poll-on-login, OI-2)
# ---------------------------------------------------------------------------


def test_notif_deferred_reminder_fires_for_patient_and_doctor(
    db, doctor_profile, patient_profile
):
    """REQ-02 AC10: check_and_fire_deferred_notifications fires appointment_reminder
    for BOTH the patient AND the assigned doctor when a matured schedule exists.
    (Issue 4 fix regression check.)"""
    # Create appointment 25 hours from now (reminder fires 24h before)
    future_appt = (datetime.utcnow() + timedelta(hours=25)).isoformat()
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=future_appt,
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt)
    db.flush()

    # Create a matured NotificationSchedule (trigger_at in the past)
    sched = NotificationSchedule(
        appointment_id=appt.appointment_id,
        trigger_type="appointment_reminder",
        trigger_at=_past_iso(hours_ago=1),  # already matured
        is_fired=0,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)

    # Fire deferred notifications as if patient just loaded a page
    check_and_fire_deferred_notifications(db, patient_profile.user_id)

    # Patient should receive the reminder
    patient_reminder = _count_notifications(
        db, patient_profile.user_id, "appointment_reminder"
    )
    # Doctor should also receive the reminder (Issue 4 fix)
    doctor_reminder = _count_notifications(
        db, doctor_profile.user_id, "appointment_reminder"
    )

    assert patient_reminder == 1, (
        f"Patient should receive 1 appointment_reminder, got {patient_reminder}"
    )
    assert doctor_reminder == 1, (
        f"Doctor should receive 1 appointment_reminder (Issue 4 fix), got {doctor_reminder}"
    )


def test_notif_deferred_reminder_does_not_fire_for_other_patient(
    db, doctor_profile, patient_profile, patient2_profile
):
    """REQ-02 AC11 / Issue 1 regression: check_and_fire_deferred_notifications
    called for patient_2 does NOT fire patient_1's appointment_reminder
    and does NOT mark patient_1's schedule as fired."""
    # Create appointment for patient 1
    appt_p1 = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=_future_iso(25),
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt_p1)
    db.flush()

    # Schedule for patient 1's appointment — already matured
    sched_p1 = NotificationSchedule(
        appointment_id=appt_p1.appointment_id,
        trigger_type="appointment_reminder",
        trigger_at=_past_iso(1),
        is_fired=0,
    )
    db.add(sched_p1)
    db.commit()
    db.refresh(sched_p1)
    original_sched_id = sched_p1.schedule_id

    # Patient 2 makes a request (triggers the poll)
    check_and_fire_deferred_notifications(db, patient2_profile.user_id)

    # Patient 1's notification must NOT have been created
    p1_reminders = _count_notifications(db, patient_profile.user_id, "appointment_reminder")
    assert p1_reminders == 0, (
        f"Issue 1 regression: patient_1's reminder fired by patient_2's login. "
        f"Count: {p1_reminders}"
    )

    # Patient 1's schedule must still be is_fired=0
    db.refresh(sched_p1)
    assert sched_p1.is_fired == 0, (
        f"Issue 1 regression: patient_1's schedule was marked fired by patient_2's login. "
        f"is_fired={sched_p1.is_fired}"
    )


def test_notif_is_fired_set_only_after_both_notifications_created(
    db, doctor_profile, patient_profile
):
    """REQ-02 AC12: NotificationSchedule.is_fired=1 only after both the patient
    AND the doctor appointment_reminder notifications exist.

    Verified by: after calling check_and_fire_deferred_notifications, assert
    is_fired=1 AND notification count = 2 (one for each party).
    """
    future_appt = _future_iso(25)
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=future_appt,
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt)
    db.flush()

    sched = NotificationSchedule(
        appointment_id=appt.appointment_id,
        trigger_type="appointment_reminder",
        trigger_at=_past_iso(1),
        is_fired=0,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)

    check_and_fire_deferred_notifications(db, patient_profile.user_id)

    # is_fired must be 1 now
    db.refresh(sched)
    assert sched.is_fired == 1, (
        f"NotificationSchedule.is_fired should be 1 after firing, got {sched.is_fired}"
    )

    # Both patient and doctor notifications must exist (is_fired set after both)
    total_reminders = (
        db.query(Notification)
        .filter(Notification.event_type == "appointment_reminder")
        .count()
    )
    assert total_reminders == 2, (
        f"Expected 2 appointment_reminder notifications (patient + doctor), "
        f"got {total_reminders}. is_fired=1 means both were created before being marked."
    )


def test_notif_deferred_reminder_not_fired_twice(
    db, doctor_profile, patient_profile
):
    """Calling check_and_fire_deferred_notifications a second time for the same
    user should not create duplicate notifications — is_fired=1 prevents re-firing."""
    future_appt = _future_iso(25)
    appt = Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=doctor_profile.doctor_id,
        scheduled_at=future_appt,
        status="Scheduled",
        created_by_user_id=patient_profile.user_id,
    )
    db.add(appt)
    db.flush()

    sched = NotificationSchedule(
        appointment_id=appt.appointment_id,
        trigger_type="appointment_reminder",
        trigger_at=_past_iso(1),
        is_fired=0,
    )
    db.add(sched)
    db.commit()

    # First fire
    check_and_fire_deferred_notifications(db, patient_profile.user_id)

    # Second fire — should be a no-op
    check_and_fire_deferred_notifications(db, patient_profile.user_id)

    patient_reminders = _count_notifications(
        db, patient_profile.user_id, "appointment_reminder"
    )
    assert patient_reminders == 1, (
        f"Double-firing: expected 1 notification, got {patient_reminders}"
    )


# ---------------------------------------------------------------------------
# Unread count includes notifications from all sources; badge shows count
# ---------------------------------------------------------------------------


def test_notif_unread_count_response_shape(
    client, db, patient_user, patient_profile
):
    """GET /notifications/unread-count returns {unread_count: N} shape."""
    resp = client.get(
        "/api/notifications/unread-count",
        headers=auth_headers(patient_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "unread_count" in data
    assert isinstance(data["unread_count"], int)
    assert data["unread_count"] == 0  # no notifications yet


def test_notif_mark_all_read_returns_marked_count(
    client, db, patient_user, patient_profile
):
    """POST /notifications/mark-all-read returns {marked_read: N}."""
    from app.services.notification_service import create_notifications

    create_notifications(db, [
        {"recipient_user_id": patient_user.id, "event_type": "invoice_created",
         "title": "T1", "body": "b", "related_entity_type": None, "related_entity_id": None},
        {"recipient_user_id": patient_user.id, "event_type": "appointment_confirmed",
         "title": "T2", "body": "b", "related_entity_type": None, "related_entity_id": None},
    ])
    db.commit()

    resp = client.post("/api/notifications/mark-all-read", headers=auth_headers(patient_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["marked_read"] == 2


def test_notif_get_notifications_empty_response(
    client, db, patient_user, patient_profile
):
    """GET /notifications for a user with no notifications returns an empty list
    with total=0."""
    resp = client.get("/api/notifications", headers=auth_headers(patient_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


def test_notif_get_notifications_unauthenticated_returns_401_or_403(
    client, db
):
    """Unauthenticated GET /notifications should be rejected."""
    resp = client.get("/api/notifications")
    assert resp.status_code in (401, 403)
