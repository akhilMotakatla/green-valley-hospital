"""REQ-11 — Patient Satisfaction Survey & Doctor Ratings.

Endpoints:
  GET  /api/patients/me/surveys                  — patient lists their surveys
  POST /api/patients/me/surveys/{survey_id}      — patient submits a survey
  GET  /api/doctor/ratings                       — doctor sees aggregate ratings
  GET  /api/admin/surveys                        — admin lists all surveys
  GET  /api/admin/surveys/{survey_id}            — admin reads one survey
  PATCH /api/admin/surveys/{survey_id}/remove-comment — admin moderates a comment

Survey rows are created by create_survey_for_appointment() (notification_service.py)
whenever an appointment transitions to 'Completed', via:
  - PATCH /api/doctor/appointments/{id}/status → 'Completed'
  - POST  /api/doctor/appointments/{id}/discharge-summary
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import (
    Appointment,
    Doctor,
    Patient,
    SatisfactionSurvey,
    User,
)
from app.utils import now_iso, paginate, total_pages

router = APIRouter(tags=["surveys"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_patient_or_403(db: Session, user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if patient is None:
        raise HTTPException(status_code=403, detail="Patient profile not found")
    return patient


def _get_doctor_or_403(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor is None:
        raise HTTPException(status_code=403, detail="Doctor profile not found")
    return doctor


def _survey_status(survey: SatisfactionSurvey) -> str:
    if survey.submitted_at is not None:
        return "submitted"
    now_str = now_iso()
    if survey.expires_at < now_str:
        return "expired"
    return "pending"


def _fmt_survey_patient(survey: SatisfactionSurvey, db: Session) -> dict:
    appt = db.get(Appointment, survey.appointment_id)
    doctor = db.get(Doctor, survey.doctor_id)
    doctor_user = db.get(User, doctor.user_id) if doctor else None
    return {
        "survey_id": survey.survey_id,
        "appointment_id": survey.appointment_id,
        "appointment_date": appt.scheduled_at[:10] if appt else None,
        "doctor_name": doctor_user.full_name if doctor_user else None,
        "trigger_after": survey.trigger_after,
        "expires_at": survey.expires_at,
        "submitted_at": survey.submitted_at,
        "status": _survey_status(survey),
    }


# ---------------------------------------------------------------------------
# Patient endpoints
# ---------------------------------------------------------------------------

@router.get("/patients/me/surveys")
def list_my_surveys(
    current_user: User = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
):
    """Patient lists all their surveys with computed status."""
    patient = _get_patient_or_403(db, current_user)

    surveys = (
        db.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.patient_id == patient.patient_id)
        .order_by(SatisfactionSurvey.survey_id.desc())
        .all()
    )
    return {"items": [_fmt_survey_patient(s, db) for s in surveys]}


class SurveySubmitRequest(BaseModel):
    doctor_star_rating: int
    overall_star_rating: int
    comment: str | None = None


@router.post("/patients/me/surveys/{survey_id}", status_code=201)
def submit_survey(
    survey_id: int,
    payload: SurveySubmitRequest,
    current_user: User = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
):
    """Patient submits a satisfaction survey."""
    patient = _get_patient_or_403(db, current_user)

    survey = db.get(SatisfactionSurvey, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")
    if survey.patient_id != patient.patient_id:
        raise HTTPException(status_code=403, detail="Not your survey")

    now_str = now_iso()

    # Validate trigger window
    if survey.trigger_after > now_str:
        raise HTTPException(
            status_code=400,
            detail="Survey is not yet available. Please check back in 24 hours after your appointment.",
        )
    if survey.expires_at < now_str:
        raise HTTPException(
            status_code=403,
            detail="Survey submission period has expired.",
        )
    if survey.submitted_at is not None:
        raise HTTPException(
            status_code=409, detail="Survey has already been submitted."
        )

    # Validate star ratings
    if not (1 <= payload.doctor_star_rating <= 5):
        raise HTTPException(
            status_code=400, detail="doctor_star_rating must be between 1 and 5"
        )
    if not (1 <= payload.overall_star_rating <= 5):
        raise HTTPException(
            status_code=400, detail="overall_star_rating must be between 1 and 5"
        )
    if payload.comment and len(payload.comment) > 1000:
        raise HTTPException(
            status_code=400, detail="comment must be 1000 characters or fewer"
        )

    survey.submitted_at = now_str
    survey.doctor_star_rating = payload.doctor_star_rating
    survey.overall_star_rating = payload.overall_star_rating
    survey.comment = payload.comment

    db.commit()
    return {"survey_id": survey.survey_id, "submitted_at": survey.submitted_at}


# ---------------------------------------------------------------------------
# Doctor endpoints
# ---------------------------------------------------------------------------

@router.get("/doctor/ratings")
def get_doctor_ratings(
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    """Doctor views their aggregate ratings and anonymized comments."""
    doctor = _get_doctor_or_403(db, current_user)

    submitted = (
        db.query(SatisfactionSurvey)
        .filter(
            SatisfactionSurvey.doctor_id == doctor.doctor_id,
            SatisfactionSurvey.submitted_at.isnot(None),
        )
        .all()
    )

    total_reviews = len(submitted)
    avg_rating = (
        round(sum(s.doctor_star_rating for s in submitted if s.doctor_star_rating) / total_reviews, 2)
        if total_reviews > 0
        else None
    )

    # Anonymized comments (no patient name), newest first
    comments = [
        {"comment": s.comment, "submitted_at": s.submitted_at}
        for s in sorted(submitted, key=lambda x: x.submitted_at or "", reverse=True)
        if s.comment and not s.is_comment_removed
    ][:20]

    return {
        "average_doctor_rating": avg_rating,
        "total_reviews": total_reviews,
        "comments": comments,
    }


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@router.get("/admin/surveys")
def admin_list_surveys(
    doctor_id: int | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    submitted_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    """Admin lists all surveys, filterable."""
    q = db.query(SatisfactionSurvey)
    if doctor_id:
        q = q.filter(SatisfactionSurvey.doctor_id == doctor_id)
    if start_date:
        q = q.filter(SatisfactionSurvey.submitted_at >= start_date)
    if end_date:
        q = q.filter(SatisfactionSurvey.submitted_at <= end_date + "Z")
    if submitted_only:
        q = q.filter(SatisfactionSurvey.submitted_at.isnot(None))
    q = q.order_by(SatisfactionSurvey.survey_id.desc())

    items_raw, total = paginate(q, page, page_size)
    items = []
    for survey in items_raw:
        patient = db.get(Patient, survey.patient_id)
        patient_user = db.get(User, patient.user_id) if patient else None
        doctor = db.get(Doctor, survey.doctor_id)
        doctor_user = db.get(User, doctor.user_id) if doctor else None
        appt = db.get(Appointment, survey.appointment_id)
        items.append({
            "survey_id": survey.survey_id,
            "appointment_id": survey.appointment_id,
            "appointment_date": appt.scheduled_at[:10] if appt else None,
            "patient_id": survey.patient_id,
            "patient_name": patient_user.full_name if patient_user else None,
            "doctor_id": survey.doctor_id,
            "doctor_name": doctor_user.full_name if doctor_user else None,
            "doctor_star_rating": survey.doctor_star_rating,
            "overall_star_rating": survey.overall_star_rating,
            "comment": None if survey.is_comment_removed else survey.comment,
            "is_comment_removed": bool(survey.is_comment_removed),
            "submitted_at": survey.submitted_at,
            "status": _survey_status(survey),
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@router.get("/admin/surveys/{survey_id}")
def admin_get_survey(
    survey_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    """Admin reads a single survey record."""
    survey = db.get(SatisfactionSurvey, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")

    patient = db.get(Patient, survey.patient_id)
    patient_user = db.get(User, patient.user_id) if patient else None
    doctor = db.get(Doctor, survey.doctor_id)
    doctor_user = db.get(User, doctor.user_id) if doctor else None
    appt = db.get(Appointment, survey.appointment_id)

    return {
        "survey_id": survey.survey_id,
        "appointment_id": survey.appointment_id,
        "appointment_date": appt.scheduled_at[:10] if appt else None,
        "patient_id": survey.patient_id,
        "patient_name": patient_user.full_name if patient_user else None,
        "doctor_id": survey.doctor_id,
        "doctor_name": doctor_user.full_name if doctor_user else None,
        "doctor_star_rating": survey.doctor_star_rating,
        "overall_star_rating": survey.overall_star_rating,
        "comment": None if survey.is_comment_removed else survey.comment,
        "is_comment_removed": bool(survey.is_comment_removed),
        "submitted_at": survey.submitted_at,
        "trigger_after": survey.trigger_after,
        "expires_at": survey.expires_at,
        "status": _survey_status(survey),
    }


@router.patch("/admin/surveys/{survey_id}/remove-comment")
def admin_remove_comment(
    survey_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    """Admin removes (nullifies) the comment from a survey. Idempotent."""
    survey = db.get(SatisfactionSurvey, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")

    survey.comment = None
    survey.is_comment_removed = 1
    db.commit()
    return {
        "survey_id": survey.survey_id,
        "is_comment_removed": True,
        "comment": None,
    }
