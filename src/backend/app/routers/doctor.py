from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import (
    Appointment,
    Doctor,
    LabOrder,
    LabResult,
    Patient,
    Prescription,
    User,
    VisitNote,
)
from app.schemas import (
    AppointmentStatusRequest,
    DoctorUpdateMeRequest,
    LabOrderCreateRequest,
    PrescriptionCreateRequest,
    VisitNoteCreateRequest,
)
from app.utils import dumps, loads, paginate, total_pages, write_audit_log

router = APIRouter(prefix="/doctor", tags=["doctor"], dependencies=[Depends(require_role("Doctor"))])


def _get_doctor_profile(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return doctor


def _has_relationship(db: Session, doctor_id: int, patient_id: int) -> bool:
    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id, Appointment.patient_id == patient_id)
        .first()
        is not None
    )


@router.get("/me")
def get_my_profile(current_user: User = Depends(require_role("Doctor")), db: Session = Depends(get_db)):
    doctor = _get_doctor_profile(db, current_user)
    return {
        "doctor_id": doctor.doctor_id,
        "full_name": current_user.full_name,
        "department": {"department_id": doctor.department.department_id, "name": doctor.department.name},
        "specialty": doctor.specialty,
        "qualifications": doctor.qualifications,
        "bio": doctor.bio,
        "years_experience": doctor.years_experience,
        "consultation_hours": doctor.consultation_hours,
        "profile_photo_path": doctor.profile_photo_path,
    }


@router.patch("/me")
def update_my_profile(payload: DoctorUpdateMeRequest, current_user: User = Depends(require_role("Doctor")), db: Session = Depends(get_db)):
    doctor = _get_doctor_profile(db, current_user)
    if payload.bio is not None:
        doctor.bio = payload.bio
    if payload.qualifications is not None:
        doctor.qualifications = payload.qualifications
    if payload.consultation_hours is not None:
        doctor.consultation_hours = payload.consultation_hours
    # v1.1: accept profile_photo_path as an optional self-service field (DOC-1, api-spec.md §4)
    if payload.profile_photo_path is not None:
        doctor.profile_photo_path = payload.profile_photo_path
    db.commit()
    return {
        "doctor_id": doctor.doctor_id,
        "bio": doctor.bio,
        "qualifications": doctor.qualifications,
        "consultation_hours": doctor.consultation_hours,
        "profile_photo_path": doctor.profile_photo_path,
    }


@router.get("/me/appointments")
def list_my_appointments(
    status_: str | None = Query(None, alias="status"),
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    query = db.query(Appointment).filter(Appointment.doctor_id == doctor.doctor_id)
    if status_:
        query = query.filter(Appointment.status == status_)
    if from_:
        query = query.filter(Appointment.scheduled_at >= from_)
    if to:
        query = query.filter(Appointment.scheduled_at <= to)
    items, total = paginate(query.order_by(Appointment.scheduled_at.desc()), page, page_size)
    result = []
    for a in items:
        patient = db.get(Patient, a.patient_id)
        result.append(
            {
                "appointment_id": a.appointment_id,
                "patient_id": a.patient_id,
                "patient_name": patient.user.full_name if patient else None,
                "scheduled_at": a.scheduled_at,
                "status": a.status,
                "reason": a.reason,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


@router.patch("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    payload: AppointmentStatusRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appointment.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")

    appointment.status = payload.status
    db.commit()
    return {"appointment_id": appointment.appointment_id, "status": appointment.status}


@router.get("/patients/{patient_id}/records")
def get_patient_records(patient_id: int, current_user: User = Depends(require_role("Doctor")), db: Session = Depends(get_db)):
    doctor = _get_doctor_profile(db, current_user)
    if not _has_relationship(db, doctor.doctor_id, patient_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No appointment relationship with this patient")

    visit_notes = db.query(VisitNote).filter(VisitNote.patient_id == patient_id, VisitNote.doctor_id == doctor.doctor_id).all()
    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id, Prescription.doctor_id == doctor.doctor_id).all()
    lab_orders = db.query(LabOrder).filter(LabOrder.patient_id == patient_id, LabOrder.doctor_id == doctor.doctor_id).all()
    order_ids = [o.order_id for o in lab_orders]
    lab_results = db.query(LabResult).filter(LabResult.order_id.in_(order_ids)).all() if order_ids else []

    return {
        "visit_notes": [
            {"record_id": v.record_id, "appointment_id": v.appointment_id, "diagnosis": v.diagnosis, "notes": v.notes, "created_at": v.created_at}
            for v in visit_notes
        ],
        "prescriptions": [
            {
                "prescription_id": p.prescription_id,
                "appointment_id": p.appointment_id,
                "medicines": loads(p.medicines_json),
                "instructions": p.instructions,
                "created_at": p.created_at,
            }
            for p in prescriptions
        ],
        "lab_results": [
            {
                "result_id": r.result_id,
                "order_id": r.order_id,
                "result_data": r.result_data,
                "file_attachment_path": r.file_attachment_path,
                "version": r.version,
                "is_finalized": bool(r.is_finalized),
                "finalized_at": r.finalized_at,
            }
            for r in lab_results
        ],
    }


@router.post("/appointments/{appointment_id}/visit-notes", status_code=status.HTTP_201_CREATED)
def create_visit_note(
    appointment_id: int,
    payload: VisitNoteCreateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appointment.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")

    note = VisitNote(
        appointment_id=appointment.appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=doctor.doctor_id,
        diagnosis=payload.diagnosis,
        notes=payload.notes,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "record_id": note.record_id,
        "appointment_id": note.appointment_id,
        "patient_id": note.patient_id,
        "doctor_id": note.doctor_id,
        "diagnosis": note.diagnosis,
        "notes": note.notes,
        "created_at": note.created_at,
    }


@router.post("/appointments/{appointment_id}/prescriptions", status_code=status.HTTP_201_CREATED)
def create_prescription(
    appointment_id: int,
    payload: PrescriptionCreateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appointment.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")

    prescription = Prescription(
        appointment_id=appointment.appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=doctor.doctor_id,
        medicines_json=dumps([m.model_dump() for m in payload.medicines]),
        instructions=payload.instructions,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return {
        "prescription_id": prescription.prescription_id,
        "appointment_id": prescription.appointment_id,
        "patient_id": prescription.patient_id,
        "doctor_id": prescription.doctor_id,
        "medicines": loads(prescription.medicines_json),
        "instructions": prescription.instructions,
        "created_at": prescription.created_at,
    }


@router.post("/patients/{patient_id}/lab-orders", status_code=status.HTTP_201_CREATED)
def create_lab_order(
    patient_id: int,
    payload: LabOrderCreateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    if not _has_relationship(db, doctor.doctor_id, patient_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No appointment relationship with this patient")

    order = LabOrder(
        patient_id=patient_id,
        doctor_id=doctor.doctor_id,
        test_type=payload.test_type,
        test_subtype=payload.test_subtype,
        status="Pending",
        notes=payload.notes,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "order_id": order.order_id,
        "patient_id": order.patient_id,
        "doctor_id": order.doctor_id,
        "test_type": order.test_type,
        "test_subtype": order.test_subtype,
        "status": order.status,
        "notes": order.notes,
        "created_at": order.created_at,
    }


@router.get("/lab-orders/{order_id}/results")
def get_lab_order_results(order_id: int, current_user: User = Depends(require_role("Doctor")), db: Session = Depends(get_db)):
    doctor = _get_doctor_profile(db, current_user)
    order = db.get(LabOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    if order.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lab order")

    results = db.query(LabResult).filter(LabResult.order_id == order_id).order_by(LabResult.version).all()
    return {
        "order_id": order.order_id,
        "status": order.status,
        "results": [
            {
                "result_id": r.result_id,
                "result_data": r.result_data,
                "file_attachment_path": r.file_attachment_path,
                "version": r.version,
                "is_finalized": bool(r.is_finalized),
                "finalized_at": r.finalized_at,
            }
            for r in results
        ],
    }
