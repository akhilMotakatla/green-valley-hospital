"""REQ-02 — Notification service helpers.

create_notifications(db, events)          — batch-insert notification rows.
check_and_fire_deferred_notifications()   — poll-on-login deferred firing
                                            (appointment reminders + surveys).

All fan-out must happen inside the same DB transaction as the triggering
action (docs/technical-design.md §4.3.1). Call create_notifications() as
the LAST step before db.commit() in any triggering endpoint.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    Notification,
    NotificationSchedule,
    Patient,
    SatisfactionSurvey,
    User,
)
from app.utils import now_iso


def create_notifications(db: Session, events: list[dict]) -> None:
    """Batch-insert notification rows.

    Each event dict must have:
        recipient_user_id: int
        event_type: str
        title: str
        body: str
        related_entity_type: str | None
        related_entity_id: int | None
    """
    for e in events:
        n = Notification(
            recipient_user_id=e["recipient_user_id"],
            event_type=e["event_type"],
            title=e["title"],
            body=e["body"],
            related_entity_type=e.get("related_entity_type"),
            related_entity_id=e.get("related_entity_id"),
        )
        db.add(n)


def check_and_fire_deferred_notifications(db: Session, user_id: int) -> None:
    """Fire matured deferred notifications for the authenticated user.

    Called on every authenticated request via GET /notifications/unread-count.

    1. appointment_reminder: notification_schedules rows where trigger_at <= now
       and the appointment belongs to this user's patient profile.
    2. survey_available: satisfaction_surveys rows where trigger_after <= now,
       submitted_at IS NULL, expires_at > now, notification_sent=0.
    """
    now = datetime.utcnow()
    now_str = now.isoformat()

    # Find patient profile for this user (may not exist for non-patient roles)
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()

    # 1. Appointment reminders
    # Issue 1 fix: scope query to the current patient's appointments only so we
    # never mark another patient's schedule as fired without sending them a
    # notification.  The query is inside the `if patient` guard for the same
    # reason — non-patient roles (Doctor, Admin, …) do not own patient-side
    # reminder schedules and should not touch them.
    pending_schedules: list = []
    if patient:
        pending_schedules = (
            db.query(NotificationSchedule)
            .join(Appointment, NotificationSchedule.appointment_id == Appointment.appointment_id)
            .filter(
                NotificationSchedule.trigger_type == "appointment_reminder",
                NotificationSchedule.trigger_at <= now_str,
                NotificationSchedule.is_fired == 0,
                Appointment.patient_id == patient.patient_id,  # Issue 1: patient-scoped
            )
            .all()
        )
        for sched in pending_schedules:
            appt = db.get(Appointment, sched.appointment_id)
            if appt is None:
                sched.is_fired = 1
                continue

            # Build doctor display name once for reuse in both notifications
            doctor_name = "your doctor"
            if appt.doctor:
                doc_user = db.get(User, appt.doctor.user_id)
                if doc_user:
                    doctor_name = doc_user.full_name

            # Fire reminder for the patient
            create_notifications(db, [{
                "recipient_user_id": user_id,
                "event_type": "appointment_reminder",
                "title": "Appointment Reminder",
                "body": (
                    f"Reminder: your appointment with {doctor_name} is coming up soon. "
                    f"Scheduled: {appt.scheduled_at[:16].replace('T', ' ')}."
                ),
                "related_entity_type": "appointment",
                "related_entity_id": appt.appointment_id,
            }])

            # Issue 4 fix: also fire reminder for the assigned doctor
            if appt.doctor_id and appt.doctor:
                patient_name = patient.user.full_name if patient.user else "a patient"
                create_notifications(db, [{
                    "recipient_user_id": appt.doctor.user_id,
                    "event_type": "appointment_reminder",
                    "title": "Appointment Reminder",
                    "body": (
                        f"Reminder: you have an appointment with {patient_name} "
                        f"scheduled at {appt.scheduled_at[:16].replace('T', ' ')}."
                    ),
                    "related_entity_type": "appointment",
                    "related_entity_id": appt.appointment_id,
                }])

            # Mark fired only after both notifications have been created
            sched.is_fired = 1

    # 2. Survey availability
    if patient:
        pending_surveys = (
            db.query(SatisfactionSurvey)
            .filter(
                SatisfactionSurvey.patient_id == patient.patient_id,
                SatisfactionSurvey.notification_sent == 0,
                SatisfactionSurvey.submitted_at.is_(None),
                SatisfactionSurvey.trigger_after <= now_str,
                SatisfactionSurvey.expires_at > now_str,
            )
            .all()
        )
        for survey in pending_surveys:
            appt = db.get(Appointment, survey.appointment_id)
            doctor_name = "your doctor"
            if appt and appt.doctor:
                doc_user = db.get(User, appt.doctor.user_id)
                if doc_user:
                    doctor_name = doc_user.full_name
            create_notifications(db, [{
                "recipient_user_id": user_id,
                "event_type": "survey_available",
                "title": "Rate Your Visit",
                "body": (
                    f"How was your appointment with {doctor_name}? "
                    f"Your feedback helps us improve. Share your rating now."
                ),
                "related_entity_type": "survey",
                "related_entity_id": survey.survey_id,
            }])
            survey.notification_sent = 1

    if pending_schedules or (patient and pending_surveys):
        db.commit()


def create_appointment_reminder_schedule(
    db: Session, appointment: Appointment
) -> None:
    """Schedule an appointment_reminder notification ~24h before the appointment.
    Called inside the appointment-creation transaction.
    """
    try:
        appt_dt = datetime.fromisoformat(appointment.scheduled_at.replace("Z", "+00:00"))
        trigger_at = (appt_dt - timedelta(hours=24)).isoformat()
    except (ValueError, AttributeError):
        return
    sched = NotificationSchedule(
        appointment_id=appointment.appointment_id,
        trigger_type="appointment_reminder",
        trigger_at=trigger_at,
        is_fired=0,
    )
    db.add(sched)


def create_survey_for_appointment(db: Session, appointment: Appointment) -> None:
    """Create a satisfaction_surveys row + notification_schedule when an
    appointment transitions to Completed. Idempotent — checks for existing row.
    Called from both:
      - POST /doctor/appointments/{id}/discharge-summary
      - PATCH /doctor/appointments/{id}/status → 'Completed'
    """
    from app.models import Doctor, SatisfactionSurvey

    # Guard: only for Completed appointments
    if appointment.status != "Completed":
        return

    # Idempotency: don't create a second survey
    existing = (
        db.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.appointment_id == appointment.appointment_id)
        .first()
    )
    if existing:
        return

    now = datetime.utcnow()
    trigger_after = (now + timedelta(hours=24)).isoformat()
    expires_at = (now + timedelta(hours=24 + 7 * 24)).isoformat()

    survey = SatisfactionSurvey(
        appointment_id=appointment.appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        trigger_after=trigger_after,
        expires_at=expires_at,
        notification_sent=0,
    )
    db.add(survey)
    db.flush()  # get survey_id

    sched = NotificationSchedule(
        survey_id=survey.survey_id,
        trigger_type="survey_available",
        trigger_at=trigger_after,
        is_fired=0,
    )
    db.add(sched)
