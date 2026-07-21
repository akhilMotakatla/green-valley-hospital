"""REQ-05 — Inter-Department Referral Management.

Endpoints:
  POST  /api/doctor/referrals                         — doctor creates referral
  GET   /api/doctor/referrals/sent                    — referring doctor's sent referrals
  GET   /api/doctor/referrals/received                — receiving dept doctor's incoming referrals
  PATCH /api/doctor/referrals/{referral_id}/accept    — receiving doctor accepts
  PATCH /api/doctor/referrals/{referral_id}/decline   — receiving doctor declines
  PATCH /api/doctor/referrals/{referral_id}/complete  — receiving doctor marks complete
  GET   /api/patients/me/referrals                    — patient's own referrals (read-only)
  GET   /api/admin/referrals                          — admin sees all (no reason field)

AUTHZ:
  Doctor: AUTHZ-2 check on create (must have appointment with patient)
  accept/decline/complete: AUTHZ-13 (caller must be in receiving department)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import (
    Appointment,
    Department,
    Doctor,
    Patient,
    Referral,
    User,
)
from app.services.notification_service import create_notifications
from app.utils import now_iso, paginate, total_pages

router = APIRouter(tags=["referrals"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ReferralCreate(BaseModel):
    patient_id: int
    to_department_id: int
    to_doctor_id: int | None = None
    reason: str
    urgency: str  # 'Routine' | 'Urgent'


class ReferralDecline(BaseModel):
    note: str


class ReferralAccept(BaseModel):
    note: str | None = None


class ReferralAdminPatch(BaseModel):
    status: str | None = None
    notes: str | None = None


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


def _referral_to_dict(r: Referral, db: Session, include_reason: bool = True) -> dict:
    referring_doc = db.get(Doctor, r.referring_doctor_id)
    referring_user = db.get(User, referring_doc.user_id) if referring_doc else None
    recv_dept = db.get(Department, r.receiving_department_id)
    recv_doc = db.get(Doctor, r.receiving_doctor_id) if r.receiving_doctor_id else None
    recv_doc_user = db.get(User, recv_doc.user_id) if recv_doc else None
    patient = db.get(Patient, r.patient_id)
    patient_user = db.get(User, patient.user_id) if patient else None

    result: dict = {
        "referral_id": r.referral_id,
        "referring_doctor_id": r.referring_doctor_id,
        "referring_doctor_name": referring_user.full_name if referring_user else None,
        "receiving_department_id": r.receiving_department_id,
        "receiving_department_name": recv_dept.name if recv_dept else None,
        "receiving_doctor_id": r.receiving_doctor_id,
        "receiving_doctor_name": recv_doc_user.full_name if recv_doc_user else None,
        "patient_id": r.patient_id,
        "patient_name": patient_user.full_name if patient_user else None,
        "urgency": r.urgency,
        "status": r.status,
        "receiving_doctor_note": r.receiving_doctor_note,
        "referred_appointment_id": r.referred_appointment_id,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }
    if include_reason:
        result["reason"] = r.reason
    return result


# ---------------------------------------------------------------------------
# POST /api/doctor/referrals
# ---------------------------------------------------------------------------

@router.post("/doctor/referrals", status_code=201)
def create_referral(
    body: ReferralCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Doctor")),
):
    doctor = _get_doctor_or_403(db, current_user)

    # AUTHZ-2: doctor must have >=1 appointment with patient
    appt = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.doctor_id,
            Appointment.patient_id == body.patient_id,
        )
        .first()
    )
    if appt is None:
        raise HTTPException(
            status_code=403,
            detail="You do not have an appointment with this patient",
        )

    # Validate urgency
    if body.urgency not in ("Routine", "Urgent"):
        raise HTTPException(status_code=400, detail="urgency must be 'Routine' or 'Urgent'")

    # Validate department
    dept = db.get(Department, body.to_department_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")

    # Validate optional receiving doctor belongs to that department
    if body.to_doctor_id is not None:
        recv_doc = db.get(Doctor, body.to_doctor_id)
        if recv_doc is None or recv_doc.department_id != body.to_department_id:
            raise HTTPException(
                status_code=400,
                detail="Receiving doctor does not belong to the specified department",
            )

    referral = Referral(
        referring_doctor_id=doctor.doctor_id,
        receiving_department_id=body.to_department_id,
        receiving_doctor_id=body.to_doctor_id,
        patient_id=body.patient_id,
        reason=body.reason,
        urgency=body.urgency,
        status="Pending",
    )
    db.add(referral)
    db.flush()  # get referral_id before notifications

    # Fan-out notification: to specific doctor or all active doctors in dept
    events: list[dict] = []
    if body.to_doctor_id is not None:
        recv_doc = db.get(Doctor, body.to_doctor_id)
        if recv_doc:
            recv_user = db.get(User, recv_doc.user_id)
            if recv_user and recv_user.is_active:
                events.append({
                    "recipient_user_id": recv_user.id,
                    "event_type": "referral_received",
                    "title": "New Referral Received",
                    "body": f"You have a new {body.urgency} referral for a patient from Dr. {current_user.full_name}.",
                    "related_entity_type": "referral",
                    "related_entity_id": referral.referral_id,
                })
    else:
        # Fan-out to all active doctors in receiving department
        dept_doctors = (
            db.query(Doctor)
            .filter(Doctor.department_id == body.to_department_id)
            .all()
        )
        for dd in dept_doctors:
            dd_user = db.get(User, dd.user_id)
            if dd_user and dd_user.is_active:
                events.append({
                    "recipient_user_id": dd_user.id,
                    "event_type": "referral_received",
                    "title": "New Referral Received",
                    "body": f"A new {body.urgency} referral has been sent to your department from Dr. {current_user.full_name}.",
                    "related_entity_type": "referral",
                    "related_entity_id": referral.referral_id,
                })

    if events:
        create_notifications(db, events)

    db.commit()
    db.refresh(referral)
    return _referral_to_dict(referral, db)


# ---------------------------------------------------------------------------
# GET /api/doctor/referrals/sent
# ---------------------------------------------------------------------------

@router.get("/doctor/referrals/sent")
def get_sent_referrals(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Doctor")),
):
    doctor = _get_doctor_or_403(db, current_user)
    q = db.query(Referral).filter(Referral.referring_doctor_id == doctor.doctor_id)
    if status:
        q = q.filter(Referral.status == status)
    q = q.order_by(Referral.created_at.desc())
    items, total = paginate(q, page, page_size)
    return {
        "items": [_referral_to_dict(r, db) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


# ---------------------------------------------------------------------------
# GET /api/doctor/referrals/received
# ---------------------------------------------------------------------------

@router.get("/doctor/referrals/received")
def get_received_referrals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Doctor")),
):
    doctor = _get_doctor_or_403(db, current_user)
    from sqlalchemy import or_
    q = (
        db.query(Referral)
        .filter(
            Referral.receiving_department_id == doctor.department_id,
            or_(
                Referral.receiving_doctor_id.is_(None),
                Referral.receiving_doctor_id == doctor.doctor_id,
            ),
        )
        # Urgent first, then by created_at
        .order_by(
            Referral.urgency.desc(),  # 'Urgent' > 'Routine' alphabetically; use case expr below
            Referral.created_at.asc(),
        )
    )
    # Actually sort Urgent first properly using CASE
    from sqlalchemy import case, text
    q = (
        db.query(Referral)
        .filter(
            Referral.receiving_department_id == doctor.department_id,
            or_(
                Referral.receiving_doctor_id.is_(None),
                Referral.receiving_doctor_id == doctor.doctor_id,
            ),
        )
        .order_by(
            case((Referral.urgency == "Urgent", 0), else_=1),
            Referral.created_at.asc(),
        )
    )
    items, total = paginate(q, page, page_size)
    return {
        "items": [_referral_to_dict(r, db) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


# ---------------------------------------------------------------------------
# PATCH /api/doctor/referrals/{referral_id}/accept
# ---------------------------------------------------------------------------

@router.patch("/doctor/referrals/{referral_id}/accept")
def accept_referral(
    referral_id: int,
    body: ReferralAccept = ReferralAccept(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Doctor")),
):
    doctor = _get_doctor_or_403(db, current_user)
    referral = db.get(Referral, referral_id)
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")

    # AUTHZ-13: caller must be in receiving department
    if doctor.department_id != referral.receiving_department_id:
        raise HTTPException(
            status_code=403,
            detail="You are not in the receiving department for this referral",
        )

    if referral.status in ("Accepted", "Declined"):
        raise HTTPException(
            status_code=409,
            detail=f"Referral is already {referral.status}",
        )

    referral.status = "Accepted"
    referral.receiving_doctor_id = doctor.doctor_id
    if body.note:
        referral.receiving_doctor_note = body.note
    referral.updated_at = now_iso()

    # Notifications: patient + referring doctor
    patient = db.get(Patient, referral.patient_id)
    patient_user = db.get(User, patient.user_id) if patient else None
    referring_doc = db.get(Doctor, referral.referring_doctor_id)
    referring_user = db.get(User, referring_doc.user_id) if referring_doc else None

    events: list[dict] = []
    if patient_user:
        events.append({
            "recipient_user_id": patient_user.id,
            "event_type": "referral_status_changed",
            "title": "Referral Accepted",
            "body": f"Your referral to {db.get(Department, referral.receiving_department_id).name} has been accepted by Dr. {current_user.full_name}.",
            "related_entity_type": "referral",
            "related_entity_id": referral_id,
        })
    if referring_user:
        events.append({
            "recipient_user_id": referring_user.id,
            "event_type": "referral_status_changed",
            "title": "Referral Accepted",
            "body": f"Your referral for patient ID {referral.patient_id} has been accepted by Dr. {current_user.full_name}.",
            "related_entity_type": "referral",
            "related_entity_id": referral_id,
        })
    create_notifications(db, events)
    db.commit()
    db.refresh(referral)
    return _referral_to_dict(referral, db)


# ---------------------------------------------------------------------------
# PATCH /api/doctor/referrals/{referral_id}/decline
# ---------------------------------------------------------------------------

@router.patch("/doctor/referrals/{referral_id}/decline")
def decline_referral(
    referral_id: int,
    body: ReferralDecline,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Doctor")),
):
    if not body.note:
        raise HTTPException(status_code=400, detail="A decline note is required")

    doctor = _get_doctor_or_403(db, current_user)
    referral = db.get(Referral, referral_id)
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")

    # AUTHZ-13
    if doctor.department_id != referral.receiving_department_id:
        raise HTTPException(
            status_code=403,
            detail="You are not in the receiving department for this referral",
        )

    if referral.status in ("Accepted", "Declined"):
        raise HTTPException(
            status_code=409,
            detail=f"Referral is already {referral.status}",
        )

    referral.status = "Declined"
    referral.receiving_doctor_note = body.note
    referral.updated_at = now_iso()

    # Notifications
    patient = db.get(Patient, referral.patient_id)
    patient_user = db.get(User, patient.user_id) if patient else None
    referring_doc = db.get(Doctor, referral.referring_doctor_id)
    referring_user = db.get(User, referring_doc.user_id) if referring_doc else None
    dept = db.get(Department, referral.receiving_department_id)

    events: list[dict] = []
    if patient_user:
        events.append({
            "recipient_user_id": patient_user.id,
            "event_type": "referral_status_changed",
            "title": "Referral Declined",
            "body": f"Your referral to {dept.name if dept else 'the department'} was declined.",
            "related_entity_type": "referral",
            "related_entity_id": referral_id,
        })
    if referring_user:
        events.append({
            "recipient_user_id": referring_user.id,
            "event_type": "referral_status_changed",
            "title": "Referral Declined",
            "body": f"Your referral for patient ID {referral.patient_id} to {dept.name if dept else 'the department'} was declined. Note: {body.note}",
            "related_entity_type": "referral",
            "related_entity_id": referral_id,
        })
    create_notifications(db, events)
    db.commit()
    db.refresh(referral)
    return _referral_to_dict(referral, db)


# ---------------------------------------------------------------------------
# PATCH /api/doctor/referrals/{referral_id}/complete
# ---------------------------------------------------------------------------

@router.patch("/doctor/referrals/{referral_id}/complete")
def complete_referral(
    referral_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Doctor")),
):
    doctor = _get_doctor_or_403(db, current_user)
    referral = db.get(Referral, referral_id)
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.receiving_doctor_id != doctor.doctor_id:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned receiving doctor can mark this referral complete",
        )

    referral.status = "Completed"
    referral.updated_at = now_iso()
    db.commit()
    db.refresh(referral)
    return _referral_to_dict(referral, db)


# ---------------------------------------------------------------------------
# GET /api/patients/me/referrals
# ---------------------------------------------------------------------------

@router.get("/patients/me/referrals")
def get_my_referrals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Patient")),
):
    patient = _get_patient_or_403(db, current_user)
    q = (
        db.query(Referral)
        .filter(Referral.patient_id == patient.patient_id)
        .order_by(Referral.created_at.desc())
    )
    items, total = paginate(q, page, page_size)
    # Patient view: no 'reason' field per OI-6
    return {
        "items": [_referral_to_dict(r, db, include_reason=False) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


# ---------------------------------------------------------------------------
# GET /api/admin/referrals
# ---------------------------------------------------------------------------

@router.get("/admin/referrals")
def admin_list_referrals(
    status: str | None = Query(default=None),
    department_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    q = db.query(Referral)
    if status:
        q = q.filter(Referral.status == status)
    if department_id:
        q = q.filter(Referral.receiving_department_id == department_id)
    q = q.order_by(Referral.created_at.desc())
    items, total = paginate(q, page, page_size)
    # Admin view: no 'reason' field per OI-6
    return {
        "items": [_referral_to_dict(r, db, include_reason=False) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }
