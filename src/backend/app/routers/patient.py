from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import CANCELLATION_NOTICE_HOURS
from app.database import get_db
from app.deps import require_role
from app.models import Appointment, Department, Doctor, IntakeForm, Invoice, LabOrder, LabResult, Patient, Prescription, User, VisitNote
from app.schemas import BookAppointmentRequest, PatientUpdateMeRequest
from app.services.availability import get_available_slots
from app.services.notification_service import create_appointment_reminder_schedule, create_notifications
from app.utils import loads, paginate, parse_iso, total_pages, utcnow

router = APIRouter(prefix="/patients", tags=["patient"], dependencies=[Depends(require_role("Patient"))])


def _get_patient_profile(db: Session, user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return patient


@router.get("/me")
def get_my_profile(current_user: User = Depends(require_role("Patient")), db: Session = Depends(get_db)):
    patient = _get_patient_profile(db, current_user)
    return {
        "patient_id": patient.patient_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "address": patient.address,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
    }


@router.patch("/me")
def update_my_profile(payload: PatientUpdateMeRequest, current_user: User = Depends(require_role("Patient")), db: Session = Depends(get_db)):
    patient = _get_patient_profile(db, current_user)
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.address is not None:
        patient.address = payload.address
    if payload.emergency_contact_name is not None:
        patient.emergency_contact_name = payload.emergency_contact_name
    if payload.emergency_contact_phone is not None:
        patient.emergency_contact_phone = payload.emergency_contact_phone
    if payload.date_of_birth is not None:
        patient.date_of_birth = payload.date_of_birth
    db.commit()
    return {
        "patient_id": patient.patient_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "address": patient.address,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
    }


@router.get("/doctors")
def browse_doctors(department_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Doctor).join(User, User.id == Doctor.user_id).filter(User.is_active == 1)
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
                "years_experience": d.years_experience,
                "profile_photo_path": d.profile_photo_path,
            }
            for d in doctors
        ]
    }


@router.get("/doctors/{doctor_id}/availability")
def doctor_availability(doctor_id: int, date: str = Query(...), db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    booked = (
        db.query(Appointment.scheduled_at)
        .filter(Appointment.doctor_id == doctor_id, Appointment.status.in_(["Scheduled", "Completed"]))
        .filter(Appointment.scheduled_at.like(f"{date}%"))
        .all()
    )
    booked_times = {b[0][11:16] for b in booked if len(b[0]) >= 16}

    slots = []
    for hour in range(9, 17):
        for minute in (0, 30):
            slot = f"{hour:02d}:{minute:02d}"
            if slot not in booked_times:
                slots.append(slot)

    return {"doctor_id": doctor_id, "date": date, "available_slots": slots}


@router.post("/me/appointments", status_code=status.HTTP_201_CREATED)
def book_appointment(payload: BookAppointmentRequest, current_user: User = Depends(require_role("Patient")), db: Session = Depends(get_db)):
    patient = _get_patient_profile(db, current_user)
    doctor = db.get(Doctor, payload.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid doctor_id")

    # REQ-01: Validate that the requested slot is currently available
    try:
        scheduled_dt = datetime.fromisoformat(payload.scheduled_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="scheduled_at must be a valid ISO-8601 datetime")

    date_str = scheduled_dt.strftime("%Y-%m-%d")
    slot_str = scheduled_dt.strftime("%H:%M")
    available_slots = get_available_slots(db, payload.doctor_id, date_str)
    if available_slots and slot_str not in available_slots:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot no longer available. Please select another time.",
        )

    appointment = Appointment(
        patient_id=patient.patient_id,
        doctor_id=payload.doctor_id,
        scheduled_at=payload.scheduled_at,
        status="Scheduled",
        reason=payload.reason,
        created_by_user_id=current_user.id,
    )
    db.add(appointment)
    db.flush()  # get appointment_id before intake form insert

    # REQ-03: Auto-create empty intake form atomically with appointment
    intake = IntakeForm(
        appointment_id=appointment.appointment_id,
        patient_id=patient.patient_id,
    )
    db.add(intake)

    # REQ-01: Schedule reminder notification ~24h before
    create_appointment_reminder_schedule(db, appointment)

    # REQ-02: Fan-out notifications to patient + doctor
    doctor_user = db.get(User, doctor.user_id)
    events = [
        {
            "recipient_user_id": current_user.id,
            "event_type": "appointment_confirmed",
            "title": "Appointment Confirmed",
            "body": (
                f"Your appointment with {doctor_user.full_name if doctor_user else 'your doctor'} "
                f"on {scheduled_dt.strftime('%b %d, %Y at %H:%M')} has been confirmed."
            ),
            "related_entity_type": "appointment",
            "related_entity_id": appointment.appointment_id,
        },
        {
            "recipient_user_id": doctor.user_id,
            "event_type": "appointment_confirmed",
            "title": "New Appointment Booked",
            "body": (
                f"A new appointment has been booked with {current_user.full_name} "
                f"on {scheduled_dt.strftime('%b %d, %Y at %H:%M')}."
            ),
            "related_entity_type": "appointment",
            "related_entity_id": appointment.appointment_id,
        },
    ]
    create_notifications(db, events)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot no longer available. Please select another time.",
        )
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


@router.get("/me/appointments")
def list_my_appointments(
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
):
    patient = _get_patient_profile(db, current_user)
    query = db.query(Appointment).filter(Appointment.patient_id == patient.patient_id)
    if status_:
        query = query.filter(Appointment.status == status_)
    items, total = paginate(query.order_by(Appointment.scheduled_at.desc()), page, page_size)
    result = []
    for a in items:
        doctor = db.get(Doctor, a.doctor_id)
        result.append(
            {
                "appointment_id": a.appointment_id,
                "doctor_id": a.doctor_id,
                "doctor_name": doctor.user.full_name if doctor else None,
                "scheduled_at": a.scheduled_at,
                "status": a.status,
                "reason": a.reason,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


@router.delete("/me/appointments/{appointment_id}")
def cancel_my_appointment(appointment_id: int, current_user: User = Depends(require_role("Patient")), db: Session = Depends(get_db)):
    patient = _get_patient_profile(db, current_user)
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appointment.patient_id != patient.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")

    scheduled_dt = parse_iso(appointment.scheduled_at)
    if scheduled_dt - utcnow() < timedelta(hours=CANCELLATION_NOTICE_HOURS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Appointments can only be cancelled at least 2 hours before the scheduled time",
        )

    appointment.status = "Cancelled"

    # REQ-02: Notify patient + doctor about cancellation
    doctor = db.get(Doctor, appointment.doctor_id)
    cancel_events: list[dict] = [
        {
            "recipient_user_id": current_user.id,
            "event_type": "appointment_cancelled",
            "title": "Appointment Cancelled",
            "body": (
                f"Your appointment on "
                f"{appointment.scheduled_at[:16].replace('T', ' ')} has been cancelled."
            ),
            "related_entity_type": "appointment",
            "related_entity_id": appointment.appointment_id,
        }
    ]
    if doctor:
        cancel_events.append({
            "recipient_user_id": doctor.user_id,
            "event_type": "appointment_cancelled",
            "title": "Appointment Cancelled",
            "body": (
                f"Appointment with {current_user.full_name} on "
                f"{appointment.scheduled_at[:16].replace('T', ' ')} has been cancelled by the patient."
            ),
            "related_entity_type": "appointment",
            "related_entity_id": appointment.appointment_id,
        })
    create_notifications(db, cancel_events)

    db.commit()
    return {"appointment_id": appointment.appointment_id, "status": appointment.status}


def _own_records(db: Session, patient_id: int) -> dict:
    visit_notes = db.query(VisitNote).filter(VisitNote.patient_id == patient_id).all()
    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
    lab_orders = db.query(LabOrder).filter(LabOrder.patient_id == patient_id).all()
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


@router.get("/me/records")
def get_my_records(current_user: User = Depends(require_role("Patient")), db: Session = Depends(get_db)):
    patient = _get_patient_profile(db, current_user)
    return _own_records(db, patient.patient_id)


@router.get("/{patient_id}/records")
def get_records_by_id(patient_id: int, current_user: User = Depends(require_role("Patient")), db: Session = Depends(get_db)):
    patient = _get_patient_profile(db, current_user)
    # AUTHZ-1 / AC-PAT-1: any patient_id other than the caller's own -> 403.
    if patient_id != patient.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view another patient's records")
    return _own_records(db, patient.patient_id)


@router.get("/me/invoices")
def list_my_invoices(
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
):
    patient = _get_patient_profile(db, current_user)
    query = db.query(Invoice).filter(Invoice.patient_id == patient.patient_id)
    if status_:
        query = query.filter(Invoice.status == status_)
    items, total = paginate(query.order_by(Invoice.created_at.desc()), page, page_size)
    return {
        "items": [
            {
                "invoice_id": inv.invoice_id,
                "appointment_id": inv.appointment_id,
                "total_amount_cents": inv.total_amount_cents,
                "status": inv.status,
                "created_at": inv.created_at,
            }
            for inv in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }
