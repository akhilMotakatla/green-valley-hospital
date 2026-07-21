"""REQ-09 — Waitlist service helpers.

trigger_waitlist_on_cancellation(db, appointment)
    Called inside the Cancelled status transition in doctor.py and staff.py.
    Finds the first FIFO 'Waiting' entry for the freed doctor+date, promotes it
    to 'Notified', sets held_slot_time and confirmation_deadline, and fires the
    waitlist_slot_available notification to the patient.

trigger_next_waitlist(db, doctor_id, preferred_date)
    Sub-helper that finds and promotes the next 'Waiting' entry for a doctor+date.
    Called after an entry expires so the slot cascades forward in the queue.

check_waitlist_expiry(db, user_id)
    Poll-on-login check: finds 'Notified' entries whose confirmation_deadline has
    passed, marks them 'Expired', re-queues the patient as a new 'Waiting' entry
    at the back, and promotes the next patient in the FIFO queue.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    Doctor,
    Patient,
    SystemConfig,
    User,
    WaitlistEntry,
)
from app.utils import now_iso


def _get_confirmation_hours(db: Session) -> int:
    row = (
        db.query(SystemConfig)
        .filter(SystemConfig.config_key == "waitlist_confirmation_hours")
        .first()
    )
    try:
        return int(row.config_value) if row else 4
    except (ValueError, TypeError):
        return 4


def _get_doctor_name(db: Session, doctor_id: int) -> str:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        return "your doctor"
    user = db.get(User, doctor.user_id)
    return user.full_name if user else "your doctor"


def _get_user_id_for_patient(db: Session, patient_id: int) -> int | None:
    patient = db.get(Patient, patient_id)
    return patient.user_id if patient else None


def trigger_waitlist_on_cancellation(db: Session, appointment: Appointment) -> None:
    """Called inside the Cancelled transition to offer a slot to the next patient."""
    from app.services.notification_service import create_notifications

    # Derive the date from scheduled_at
    try:
        appt_dt = datetime.fromisoformat(appointment.scheduled_at.replace("Z", "+00:00"))
        preferred_date = appt_dt.strftime("%Y-%m-%d")
        held_time = appt_dt.strftime("%H:%M")
    except (ValueError, AttributeError):
        return

    trigger_next_waitlist(db, appointment.doctor_id, preferred_date, held_time)


def trigger_next_waitlist(
    db: Session,
    doctor_id: int,
    preferred_date: str,
    held_slot_time: str | None = None,
) -> None:
    """Promote the first 'Waiting' entry for doctor+date to 'Notified'."""
    from app.services.notification_service import create_notifications

    entry = (
        db.query(WaitlistEntry)
        .filter(
            WaitlistEntry.doctor_id == doctor_id,
            WaitlistEntry.preferred_date == preferred_date,
            WaitlistEntry.status == "Waiting",
        )
        .order_by(WaitlistEntry.created_at.asc())
        .first()
    )
    if entry is None:
        return

    hours = _get_confirmation_hours(db)
    now = datetime.utcnow()
    deadline = now + timedelta(hours=hours)

    entry.status = "Notified"
    entry.notified_at = now.isoformat()
    entry.confirmation_deadline = deadline.isoformat()
    if held_slot_time is not None:
        entry.held_slot_time = held_slot_time

    doctor_name = _get_doctor_name(db, doctor_id)
    user_id = _get_user_id_for_patient(db, entry.patient_id)
    if user_id is None:
        return

    create_notifications(db, [
        {
            "recipient_user_id": user_id,
            "event_type": "waitlist_slot_available",
            "title": "A slot is available!",
            "body": (
                f"A slot opened with Dr. {doctor_name} on {preferred_date}. "
                f"Confirm by {deadline.strftime('%H:%M UTC')}."
            ),
            "related_entity_type": "waitlist_entry",
            "related_entity_id": entry.entry_id,
        }
    ])


def check_waitlist_expiry(db: Session, user_id: int) -> None:
    """Poll-on-login: expire overdue 'Notified' entries and cascade to next patient."""
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if patient is None:
        return

    now_str = datetime.utcnow().isoformat()

    expired_entries = (
        db.query(WaitlistEntry)
        .filter(
            WaitlistEntry.patient_id == patient.patient_id,
            WaitlistEntry.status == "Notified",
            WaitlistEntry.confirmation_deadline < now_str,
        )
        .all()
    )

    for entry in expired_entries:
        # Mark this entry as expired
        entry.status = "Expired"

        # Re-add patient at back of queue with a fresh 'Waiting' entry
        new_entry = WaitlistEntry(
            patient_id=entry.patient_id,
            doctor_id=entry.doctor_id,
            preferred_date=entry.preferred_date,
            status="Waiting",
            created_at=now_iso(),
        )
        db.add(new_entry)
        db.flush()

        # Promote the next patient in FIFO for this slot
        # (the new entry for this patient is at the back, so it won't be re-picked immediately)
        trigger_next_waitlist(
            db, entry.doctor_id, entry.preferred_date, entry.held_slot_time
        )

    if expired_entries:
        db.commit()
