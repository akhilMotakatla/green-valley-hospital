"""REQ-04 — Vitals Trend Visualization (backend).

Endpoints:
  POST /api/patients/{patient_id}/vitals   — Staff/Admin record vitals
  GET  /api/patients/{patient_id}/vitals   — Doctor (own patients), Staff, Admin
  GET  /api/appointments/{appointment_id}/vitals — single appointment vitals

AUTHZ rules:
  POST: Staff, Admin only
  GET (patient):  Doctor (must have >=1 appointment with patient), Staff, Admin
  GET (appointment): same as GET patient
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Appointment, Doctor, Patient, User, Vitals
from app.utils import now_iso, paginate, total_pages

router = APIRouter(tags=["vitals"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class VitalsPost(BaseModel):
    appointment_id: int | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    weight_kg: float | None = None
    pulse_bpm: int | None = None
    temperature_celsius: float | None = None
    height_cm: float | None = None


class VitalsOut(BaseModel):
    vital_id: int
    patient_id: int
    appointment_id: int | None
    recorded_by_user_id: int
    systolic_bp: int | None
    diastolic_bp: int | None
    weight_kg: float | None
    pulse_bpm: int | None
    temperature_celsius: float | None
    height_cm: float | None
    recorded_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_patient_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _assert_can_read_vitals(patient_id: int, current_user: User, db: Session) -> None:
    role = current_user.role
    if role in ("Staff", "Admin"):
        return
    if role == "Doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor is None:
            raise HTTPException(status_code=403, detail="Doctor profile not found")
        # AUTHZ-2: doctor must have at least one appointment with this patient
        appt = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor.doctor_id,
                Appointment.patient_id == patient_id,
            )
            .first()
        )
        if appt is None:
            raise HTTPException(
                status_code=403,
                detail="You do not have an appointment with this patient",
            )
        return
    raise HTTPException(status_code=403, detail="Not authorized")


def _vitals_out(v: Vitals) -> VitalsOut:
    return VitalsOut(
        vital_id=v.vital_id,
        patient_id=v.patient_id,
        appointment_id=v.appointment_id,
        recorded_by_user_id=v.recorded_by_user_id,
        systolic_bp=v.systolic_bp,
        diastolic_bp=v.diastolic_bp,
        weight_kg=v.weight_kg,
        pulse_bpm=v.pulse_bpm,
        temperature_celsius=v.temperature_celsius,
        height_cm=v.height_cm,
        recorded_at=v.recorded_at,
    )


# ---------------------------------------------------------------------------
# POST /api/patients/{patient_id}/vitals
# ---------------------------------------------------------------------------

@router.post("/patients/{patient_id}/vitals", response_model=VitalsOut, status_code=201)
def post_vitals(
    patient_id: int,
    body: VitalsPost,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("Staff", "Admin"):
        raise HTTPException(status_code=403, detail="Only Staff or Admin can record vitals")

    _require_patient_or_404(db, patient_id)

    # At least one measurement required
    measurements = [
        body.systolic_bp, body.diastolic_bp, body.weight_kg,
        body.pulse_bpm, body.temperature_celsius, body.height_cm,
    ]
    if all(m is None for m in measurements):
        raise HTTPException(
            status_code=400,
            detail="At least one measurement field must be provided",
        )

    # BP both-or-neither rule
    if (body.systolic_bp is None) != (body.diastolic_bp is None):
        raise HTTPException(
            status_code=400,
            detail="systolic_bp and diastolic_bp must both be provided or both omitted",
        )

    # Range validations per VITFR-2/3
    errors: list[str] = []
    if body.pulse_bpm is not None and not (20 <= body.pulse_bpm <= 300):
        errors.append("pulse_bpm must be between 20 and 300")
    if body.temperature_celsius is not None and not (30.0 <= body.temperature_celsius <= 45.0):
        errors.append("temperature_celsius must be between 30.0 and 45.0")
    if body.weight_kg is not None and body.weight_kg <= 0:
        errors.append("weight_kg must be greater than 0")
    if body.height_cm is not None and body.height_cm <= 0:
        errors.append("height_cm must be greater than 0")
    if body.systolic_bp is not None and not (40 <= body.systolic_bp <= 300):
        errors.append("systolic_bp must be between 40 and 300")
    if body.diastolic_bp is not None and not (40 <= body.diastolic_bp <= 300):
        errors.append("diastolic_bp must be between 40 and 300")
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    # Optional: verify appointment belongs to patient
    if body.appointment_id is not None:
        appt = db.get(Appointment, body.appointment_id)
        if appt is None or appt.patient_id != patient_id:
            raise HTTPException(status_code=400, detail="Appointment not found for this patient")

    v = Vitals(
        patient_id=patient_id,
        appointment_id=body.appointment_id,
        recorded_by_user_id=current_user.id,
        systolic_bp=body.systolic_bp,
        diastolic_bp=body.diastolic_bp,
        weight_kg=body.weight_kg,
        pulse_bpm=body.pulse_bpm,
        temperature_celsius=body.temperature_celsius,
        height_cm=body.height_cm,
        recorded_at=now_iso(),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return _vitals_out(v)


# ---------------------------------------------------------------------------
# GET /api/patients/{patient_id}/vitals
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}/vitals")
def get_patient_vitals(
    patient_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient_or_404(db, patient_id)
    _assert_can_read_vitals(patient_id, current_user, db)

    q = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(Vitals.recorded_at.asc())
    )
    items, total = paginate(q, page, page_size)
    return {
        "items": [_vitals_out(v) for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


# ---------------------------------------------------------------------------
# GET /api/appointments/{appointment_id}/vitals
# ---------------------------------------------------------------------------

@router.get("/appointments/{appointment_id}/vitals")
def get_appointment_vitals(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = db.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    _assert_can_read_vitals(appt.patient_id, current_user, db)

    records = (
        db.query(Vitals)
        .filter(Vitals.appointment_id == appointment_id)
        .order_by(Vitals.recorded_at.asc())
        .all()
    )
    return {"items": [_vitals_out(v) for v in records]}
