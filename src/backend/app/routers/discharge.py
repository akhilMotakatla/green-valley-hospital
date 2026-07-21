"""REQ-10 — Discharge Summary & Follow-Up Scheduling.

Endpoints:
  POST /api/doctor/appointments/{appointment_id}/discharge-summary
       Doctor submits discharge summary (with optional follow-up booking).
       Atomic: summary + follow-up appointment created in one transaction.

  GET  /api/doctor/appointments/{appointment_id}/discharge-summary
       Doctor reads the discharge summary for an appointment.

  GET  /api/patients/me/discharge-summaries
       Patient lists all their own discharge summaries (paginated).

  GET  /api/patients/me/appointments/{appointment_id}/discharge-summary
       Patient reads a specific discharge summary for one of their appointments.

Survey row creation is handled by create_survey_for_appointment() from
notification_service, called on the 'Completed' status transition in doctor.py.
That same helper is also called in the POST handler here (discharge path).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import (
    Appointment,
    DischargeSummary,
    Doctor,
    Patient,
    User,
)
from app.services.availability import get_available_slots
from app.services.notification_service import create_notifications, create_survey_for_appointment
from app.utils import now_iso, paginate, total_pages

router = APIRouter(tags=["discharge"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_doctor_or_403(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor is None:
        raise HTTPException(status_code=403, detail="Doctor profile not found")
    return doctor


def _get_patient_or_403(db: Session, user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if patient is None:
        raise HTTPException(status_code=403, detail="Patient profile not found")
    return patient


def _fmt_summary(summary: DischargeSummary) -> dict:
    return {
        "summary_id": summary.summary_id,
        "appointment_id": summary.appointment_id,
        "patient_id": summary.patient_id,
        "doctor_id": summary.doctor_id,
        "key_findings": summary.key_findings,
        "patient_instructions": summary.patient_instructions,
        "activity_restrictions": summary.activity_restrictions,
        "medication_reminders": summary.medication_reminders,
        "follow_up_appointment_id": summary.follow_up_appointment_id,
        "created_at": summary.created_at,
    }


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class FollowUpRequest(BaseModel):
    scheduled_at: str  # ISO-8601 datetime


class DischargeSummaryCreateRequest(BaseModel):
    key_findings: str
    patient_instructions: str | None = None
    activity_restrictions: str | None = None
    medication_reminders: str | None = None
    follow_up: FollowUpRequest | None = None


# ---------------------------------------------------------------------------
# Doctor endpoints
# ---------------------------------------------------------------------------

@router.post("/doctor/appointments/{appointment_id}/discharge-summary", status_code=201)
def create_discharge_summary(
    appointment_id: int,
    payload: DischargeSummaryCreateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    """Doctor submits a discharge summary, optionally booking a follow-up appointment.

    Atomic transaction per OI-8:
    1. Validate appointment is Completed + belongs to calling doctor.
    2. Check no existing discharge summary.
    3. If follow_up provided: validate slot availability.
       If slot taken: 409 + rollback (no partial state).
    4. INSERT follow-up appointment (if requested).
    5. INSERT discharge_summaries row.
    6. CREATE notifications.
    7. CREATE satisfaction_surveys row + notification_schedule.
    8. COMMIT.
    """
    doctor = _get_doctor_or_403(db, current_user)

    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=403, detail="Not your appointment")
    if appointment.status != "Completed":
        raise HTTPException(
            status_code=400, detail="Discharge summary can only be created for Completed appointments"
        )

    # Idempotency guard
    existing = (
        db.query(DischargeSummary)
        .filter(DischargeSummary.appointment_id == appointment_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="A discharge summary already exists for this appointment"
        )

    follow_up_appointment: Appointment | None = None

    if payload.follow_up:
        # Validate the follow-up slot
        fu_scheduled_at = payload.follow_up.scheduled_at
        try:
            from datetime import datetime as _dt
            fu_dt = _dt.fromisoformat(fu_scheduled_at.replace("Z", "+00:00"))
            fu_date = fu_dt.strftime("%Y-%m-%d")
            fu_time = fu_dt.strftime("%H:%M")
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="follow_up.scheduled_at must be a valid ISO-8601 datetime")

        available = get_available_slots(db, doctor.doctor_id, fu_date)
        if fu_time not in available:
            raise HTTPException(
                status_code=409, detail="Follow-up slot is no longer available."
            )

        # Get the patient for this appointment
        patient = db.get(Patient, appointment.patient_id)
        if patient is None:
            raise HTTPException(status_code=400, detail="Patient not found")

        follow_up_appointment = Appointment(
            patient_id=appointment.patient_id,
            doctor_id=doctor.doctor_id,
            scheduled_at=fu_scheduled_at,
            status="Scheduled",
            reason="Follow-up appointment",
            created_by_user_id=current_user.id,
            created_at=now_iso(),
        )
        db.add(follow_up_appointment)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409, detail="Follow-up slot is no longer available."
            )

    # Create the discharge summary
    summary = DischargeSummary(
        appointment_id=appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=doctor.doctor_id,
        key_findings=payload.key_findings,
        patient_instructions=payload.patient_instructions,
        activity_restrictions=payload.activity_restrictions,
        medication_reminders=payload.medication_reminders,
        follow_up_appointment_id=(
            follow_up_appointment.appointment_id if follow_up_appointment else None
        ),
        created_at=now_iso(),
    )
    db.add(summary)

    # Notifications
    patient = db.get(Patient, appointment.patient_id)
    patient_user = db.get(User, patient.user_id) if patient else None
    doctor_user = db.get(User, doctor.user_id)

    notif_events = []
    if patient_user:
        notif_events.append({
            "recipient_user_id": patient_user.id,
            "event_type": "discharge_summary_ready",
            "title": "Discharge Summary Ready",
            "body": "Your doctor has prepared a discharge summary for your recent visit. View it in your appointments.",
            "related_entity_type": "appointment",
            "related_entity_id": appointment_id,
        })

    if follow_up_appointment and patient_user:
        notif_events.append({
            "recipient_user_id": patient_user.id,
            "event_type": "follow_up_booked",
            "title": "Follow-Up Appointment Booked",
            "body": (
                f"A follow-up appointment has been scheduled for "
                f"{follow_up_appointment.scheduled_at[:16].replace('T', ' ')}."
            ),
            "related_entity_type": "appointment",
            "related_entity_id": follow_up_appointment.appointment_id,
        })
        if doctor_user:
            notif_events.append({
                "recipient_user_id": doctor_user.id,
                "event_type": "follow_up_booked",
                "title": "Follow-Up Appointment Booked",
                "body": (
                    f"A follow-up appointment was booked for "
                    f"{patient_user.full_name if patient_user else 'patient'} "
                    f"on {follow_up_appointment.scheduled_at[:16].replace('T', ' ')}."
                ),
                "related_entity_type": "appointment",
                "related_entity_id": follow_up_appointment.appointment_id,
            })

    if notif_events:
        create_notifications(db, notif_events)

    # Create satisfaction survey row (idempotent)
    create_survey_for_appointment(db, appointment)

    db.commit()
    db.refresh(summary)
    return _fmt_summary(summary)


@router.get("/doctor/appointments/{appointment_id}/discharge-summary")
def get_discharge_summary_doctor(
    appointment_id: int,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    """Doctor reads the discharge summary for one of their appointments."""
    doctor = _get_doctor_or_403(db, current_user)

    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    summary = (
        db.query(DischargeSummary)
        .filter(DischargeSummary.appointment_id == appointment_id)
        .first()
    )
    if summary is None:
        raise HTTPException(status_code=404, detail="No discharge summary for this appointment")
    return _fmt_summary(summary)


# ---------------------------------------------------------------------------
# Patient endpoints
# ---------------------------------------------------------------------------

@router.get("/patients/me/discharge-summaries")
def list_my_discharge_summaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
):
    """Patient lists all their own discharge summaries."""
    patient = _get_patient_or_403(db, current_user)

    q = (
        db.query(DischargeSummary)
        .filter(DischargeSummary.patient_id == patient.patient_id)
        .order_by(DischargeSummary.created_at.desc())
    )
    items_raw, total = paginate(q, page, page_size)

    items = []
    for summary in items_raw:
        appt = db.get(Appointment, summary.appointment_id)
        doctor = db.get(Doctor, summary.doctor_id)
        doctor_user = db.get(User, doctor.user_id) if doctor else None
        d = _fmt_summary(summary)
        d["appointment_scheduled_at"] = appt.scheduled_at if appt else None
        d["doctor_name"] = doctor_user.full_name if doctor_user else None
        items.append(d)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@router.get("/patients/me/appointments/{appointment_id}/discharge-summary")
def get_my_discharge_summary(
    appointment_id: int,
    current_user: User = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
):
    """Patient reads the discharge summary for one of their own appointments."""
    patient = _get_patient_or_403(db, current_user)

    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.patient_id != patient.patient_id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    summary = (
        db.query(DischargeSummary)
        .filter(DischargeSummary.appointment_id == appointment_id)
        .first()
    )
    if summary is None:
        raise HTTPException(status_code=404, detail="No discharge summary for this appointment")

    doctor = db.get(Doctor, summary.doctor_id)
    doctor_user = db.get(User, doctor.user_id) if doctor else None
    d = _fmt_summary(summary)
    d["doctor_name"] = doctor_user.full_name if doctor_user else None
    return d
