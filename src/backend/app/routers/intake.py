"""REQ-03 — Patient Pre-Visit Intake Form.

Endpoints:
  GET   /api/appointments/{appointment_id}/intake  — read form
  PATCH /api/appointments/{appointment_id}/intake  — patient submits/updates form

Auto-creation of the intake_forms row happens inside POST /api/appointments
(TASK-005 / patient.py). This router only adds the read and update endpoints.

Access rules:
  GET:   Patient (own appointment), Doctor (assigned to appointment), Staff, Admin
  PATCH: Patient only; 403 if appointment.status == 'Completed'
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Appointment, Doctor, IntakeForm, Patient, User
from app.utils import now_iso

router = APIRouter(tags=["intake"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class IntakePatch(BaseModel):
    chief_complaint: str | None = None
    symptom_duration: str | None = None
    allergies: str | None = None
    current_medications: str | None = None
    pain_scale: int | None = Field(default=None, ge=1, le=10)
    additional_notes: str | None = None
    submit: bool = False


class IntakeOut(BaseModel):
    submitted: bool
    intake_form_id: int | None = None
    appointment_id: int | None = None
    chief_complaint: str | None = None
    symptom_duration: str | None = None
    allergies: str | None = None
    current_medications: str | None = None
    pain_scale: int | None = None
    additional_notes: str | None = None
    submitted_at: str | None = None
    created_at: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


def _assert_can_read(appt: Appointment, current_user: User, db: Session) -> None:
    """Raises 403 if the caller is not allowed to read this appointment's intake form."""
    role = current_user.role
    if role == "Admin" or role == "Staff":
        return
    if role == "Patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient is None or patient.patient_id != appt.patient_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return
    if role == "Doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor is None or doctor.doctor_id != appt.doctor_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return
    raise HTTPException(status_code=403, detail="Not authorized")


# ---------------------------------------------------------------------------
# GET /api/appointments/{appointment_id}/intake
# ---------------------------------------------------------------------------

@router.get("/appointments/{appointment_id}/intake", response_model=IntakeOut)
def get_intake(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = _get_appointment_or_404(db, appointment_id)
    _assert_can_read(appt, current_user, db)

    form = db.query(IntakeForm).filter(IntakeForm.appointment_id == appointment_id).first()
    if form is None:
        return IntakeOut(submitted=False)

    return IntakeOut(
        submitted=form.submitted_at is not None,
        intake_form_id=form.intake_form_id,
        appointment_id=form.appointment_id,
        chief_complaint=form.chief_complaint,
        symptom_duration=form.symptom_duration,
        allergies=form.allergies,
        current_medications=form.current_medications,
        pain_scale=form.pain_scale,
        additional_notes=form.additional_notes,
        submitted_at=form.submitted_at,
        created_at=form.created_at,
    )


# ---------------------------------------------------------------------------
# PATCH /api/appointments/{appointment_id}/intake
# ---------------------------------------------------------------------------

@router.patch("/appointments/{appointment_id}/intake", response_model=IntakeOut)
def patch_intake(
    appointment_id: int,
    body: IntakePatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=403, detail="Only patients can update intake forms")

    appt = _get_appointment_or_404(db, appointment_id)

    # Patient must own this appointment
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if patient is None or patient.patient_id != appt.patient_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Read-only once Completed
    if appt.status == "Completed":
        raise HTTPException(
            status_code=403,
            detail="Intake form is read-only once appointment is Completed",
        )

    form = db.query(IntakeForm).filter(IntakeForm.appointment_id == appointment_id).first()
    if form is None:
        # Should not happen in normal flow (auto-created on booking), but handle gracefully
        form = IntakeForm(appointment_id=appointment_id, patient_id=patient.patient_id)
        db.add(form)

    # Apply partial updates
    if body.chief_complaint is not None:
        form.chief_complaint = body.chief_complaint
    if body.symptom_duration is not None:
        form.symptom_duration = body.symptom_duration
    if body.allergies is not None:
        form.allergies = body.allergies
    if body.current_medications is not None:
        form.current_medications = body.current_medications
    if body.pain_scale is not None:
        form.pain_scale = body.pain_scale
    if body.additional_notes is not None:
        form.additional_notes = body.additional_notes

    if body.submit:
        # Validate required fields on submission
        if not form.chief_complaint or not form.symptom_duration:
            raise HTTPException(
                status_code=400,
                detail="chief_complaint and symptom_duration are required to submit",
            )
        form.submitted_at = now_iso()

    db.commit()
    db.refresh(form)

    return IntakeOut(
        submitted=form.submitted_at is not None,
        intake_form_id=form.intake_form_id,
        appointment_id=form.appointment_id,
        chief_complaint=form.chief_complaint,
        symptom_duration=form.symptom_duration,
        allergies=form.allergies,
        current_medications=form.current_medications,
        pain_scale=form.pain_scale,
        additional_notes=form.additional_notes,
        submitted_at=form.submitted_at,
        created_at=form.created_at,
    )
