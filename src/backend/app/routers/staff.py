from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import (
    Appointment,
    ContactMessage,
    Department,
    Doctor,
    LabOrder,
    LabResult,
    Patient,
    Prescription,
    User,
    Vitals,
)
from app.schemas import (
    ContactMessageStatusRequest,
    StaffAppointmentCreateRequest,
    StaffAppointmentUpdateRequest,
    StaffPatientCreateRequest,
    VitalsCreateRequest,
)
from app.security import hash_password
from app.utils import loads, paginate, total_pages

router = APIRouter(prefix="/staff", tags=["staff"], dependencies=[Depends(require_role("Staff"))])


@router.post("/patients", status_code=status.HTTP_201_CREATED)
def register_walk_in_patient(payload: StaffPatientCreateRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already registered")

    temp_password = secrets.token_urlsafe(9)
    user = User(
        email=payload.email,
        password_hash=hash_password(temp_password),
        role="Patient",
        full_name=payload.full_name,
        phone=payload.phone,
        is_active=1,
    )
    db.add(user)
    db.flush()

    patient = Patient(
        user_id=user.id,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        address=payload.address,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return {
        "patient_id": patient.patient_id,
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "temporary_password": temp_password,
    }


@router.get("/patients/{patient_id}")
def get_patient_basic_info(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    upcoming = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id, Appointment.status == "Scheduled")
        .order_by(Appointment.scheduled_at)
        .all()
    )
    return {
        "patient_id": patient.patient_id,
        "full_name": patient.user.full_name,
        "email": patient.user.email,
        "phone": patient.user.phone,
        "date_of_birth": patient.date_of_birth,
        "upcoming_appointments": [
            {"appointment_id": a.appointment_id, "doctor_id": a.doctor_id, "scheduled_at": a.scheduled_at, "status": a.status}
            for a in upcoming
        ],
    }


@router.get("/patients")
def search_patients(search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Patient).join(User, User.id == Patient.user_id)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.full_name.like(like), User.email.like(like)))
    items, total = paginate(query, page, page_size)
    return {
        "items": [
            {"patient_id": p.patient_id, "full_name": p.user.full_name, "email": p.user.email, "phone": p.user.phone}
            for p in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment_for_patient(payload: StaffAppointmentCreateRequest, current_user: User = Depends(require_role("Staff")), db: Session = Depends(get_db)):
    if db.get(Patient, payload.patient_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid patient_id")
    if db.get(Doctor, payload.doctor_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid doctor_id")

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.scheduled_at == payload.scheduled_at,
            Appointment.status.in_(["Scheduled", "Completed"]),
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This time slot is already booked for the selected doctor")

    appointment = Appointment(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        scheduled_at=payload.scheduled_at,
        status="Scheduled",
        reason=payload.reason,
        created_by_user_id=current_user.id,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This time slot is already booked for the selected doctor")
    db.refresh(appointment)
    return {
        "appointment_id": appointment.appointment_id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "scheduled_at": appointment.scheduled_at,
        "status": appointment.status,
        "reason": appointment.reason,
        "created_at": appointment.created_at,
    }


@router.get("/appointments")
def list_appointments(
    patient_id: int | None = None,
    doctor_id: int | None = None,
    date: str | None = None,
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status_:
        query = query.filter(Appointment.status == status_)
    if date:
        query = query.filter(Appointment.scheduled_at.like(f"{date}%"))
    items, total = paginate(query.order_by(Appointment.scheduled_at.desc()), page, page_size)
    result = []
    for a in items:
        patient = db.get(Patient, a.patient_id)
        doctor = db.get(Doctor, a.doctor_id)
        result.append(
            {
                "appointment_id": a.appointment_id,
                "patient_id": a.patient_id,
                "patient_name": patient.user.full_name if patient else None,
                "doctor_id": a.doctor_id,
                "doctor_name": doctor.user.full_name if doctor else None,
                "scheduled_at": a.scheduled_at,
                "status": a.status,
                "reason": a.reason,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


@router.patch("/appointments/{appointment_id}")
def update_appointment(appointment_id: int, payload: StaffAppointmentUpdateRequest, db: Session = Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Front-desk override: no notice-window restriction (architecture.md §4.1).
    if payload.scheduled_at is not None:
        appointment.scheduled_at = payload.scheduled_at
    if payload.doctor_id is not None:
        appointment.doctor_id = payload.doctor_id
    if payload.status is not None:
        appointment.status = payload.status
    if payload.reason is not None:
        appointment.reason = payload.reason

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This time slot is already booked for the selected doctor")

    return {
        "appointment_id": appointment.appointment_id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "scheduled_at": appointment.scheduled_at,
        "status": appointment.status,
        "reason": appointment.reason,
    }


@router.post("/patients/{patient_id}/vitals", status_code=status.HTTP_201_CREATED)
def record_vitals(patient_id: int, payload: VitalsCreateRequest, current_user: User = Depends(require_role("Staff")), db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    vitals = Vitals(
        patient_id=patient_id,
        recorded_by_user_id=current_user.id,
        recorded_for_appointment_id=payload.recorded_for_appointment_id,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        blood_pressure=payload.blood_pressure,
        temperature_c=payload.temperature_c,
        pulse_bpm=payload.pulse_bpm,
    )
    db.add(vitals)
    db.commit()
    db.refresh(vitals)
    return {
        "vitals_id": vitals.vitals_id,
        "patient_id": vitals.patient_id,
        "height_cm": vitals.height_cm,
        "weight_kg": vitals.weight_kg,
        "blood_pressure": vitals.blood_pressure,
        "temperature_c": vitals.temperature_c,
        "pulse_bpm": vitals.pulse_bpm,
        "recorded_by_user_id": vitals.recorded_by_user_id,
        "created_at": vitals.created_at,
    }


@router.get("/patients/{patient_id}/prescriptions")
def get_patient_prescriptions(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
    return {
        "items": [
            {
                "prescription_id": p.prescription_id,
                "appointment_id": p.appointment_id,
                "doctor_id": p.doctor_id,
                "medicines": loads(p.medicines_json),
                "instructions": p.instructions,
                "created_at": p.created_at,
            }
            for p in prescriptions
        ]
    }


@router.get("/patients/{patient_id}/lab-results")
def get_patient_lab_results(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    order_ids = [o.order_id for o in db.query(LabOrder).filter(LabOrder.patient_id == patient_id).all()]
    results = db.query(LabResult).filter(LabResult.order_id.in_(order_ids)).all() if order_ids else []
    return {
        "items": [
            {
                "result_id": r.result_id,
                "order_id": r.order_id,
                "result_data": r.result_data,
                "file_attachment_path": r.file_attachment_path,
                "version": r.version,
                "is_finalized": bool(r.is_finalized),
                "finalized_at": r.finalized_at,
            }
            for r in results
        ]
    }


@router.get("/contact-messages")
def list_contact_messages(status_: str | None = Query(None, alias="status"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(ContactMessage)
    if status_:
        query = query.filter(ContactMessage.status == status_)
    items, total = paginate(query.order_by(ContactMessage.created_at.desc()), page, page_size)
    return {
        "items": [
            {
                "message_id": m.message_id,
                "name": m.name,
                "email": m.email,
                "phone": m.phone,
                "subject": m.subject,
                "message": m.message,
                "status": m.status,
                "created_at": m.created_at,
            }
            for m in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/contact-messages/{message_id}/status")
def update_contact_message_status(message_id: int, payload: ContactMessageStatusRequest, db: Session = Depends(get_db)):
    message = db.get(ContactMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    message.status = payload.status
    db.commit()
    return {"message_id": message.message_id, "status": message.status}


@router.get("/directory")
def doctor_directory(department_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Doctor)
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    doctors = query.all()
    return {
        "items": [
            {
                "doctor_id": d.doctor_id,
                "full_name": d.user.full_name,
                "specialty": d.specialty,
                "department_name": d.department.name,
                "consultation_hours": d.consultation_hours,
                "profile_photo_path": d.profile_photo_path,
            }
            for d in doctors
        ]
    }
