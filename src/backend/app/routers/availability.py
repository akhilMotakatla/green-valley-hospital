"""REQ-01 — Doctor Availability & Slot Management.

Exposes:
  - GET  /doctors/{doctor_id}/available-slots   (Patient/Staff/Doctor/Admin)
  - Doctor-scoped schedule / config / block endpoints  (/doctor/availability/*)
  - Admin-scoped counterparts (/admin/doctors/{doctor_id}/availability/*)

All slot logic is delegated to app.services.availability.get_available_slots().
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import (
    Doctor,
    DoctorAvailabilityBlock,
    DoctorAvailabilitySchedule,
    DoctorSlotConfig,
    User,
)
from app.services.availability import get_available_slots
from app.utils import now_iso

# ---------------------------------------------------------------------------
# Sub-router: public slot query (Patient/Staff/Doctor/Admin)
# ---------------------------------------------------------------------------

slots_router = APIRouter(tags=["availability"])


@slots_router.get("/doctors/{doctor_id}/available-slots")
def get_doctor_available_slots(
    doctor_id: int,
    date: str = Query(..., description="YYYY-MM-DD"),
    current_user: User = Depends(
        require_role("Patient", "Staff", "Doctor", "Admin")
    ),
    db: Session = Depends(get_db),
):
    """Return available HH:MM slot list for a doctor on a given date."""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    config = (
        db.query(DoctorSlotConfig)
        .filter(DoctorSlotConfig.doctor_id == doctor_id)
        .first()
    )
    slot_minutes = config.slot_duration_minutes if config else 30

    slots = get_available_slots(db, doctor_id, date)
    return {
        "doctor_id": doctor_id,
        "date": date,
        "slot_duration_minutes": slot_minutes,
        "slots": slots,
    }


# ---------------------------------------------------------------------------
# Doctor-scoped router (/doctor/availability/*)
# ---------------------------------------------------------------------------

doctor_avail_router = APIRouter(
    prefix="/doctor/availability",
    tags=["availability"],
)


def _get_doctor_profile(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor


def _fmt_schedule(s: DoctorAvailabilitySchedule) -> dict:
    return {
        "schedule_id": s.schedule_id,
        "doctor_id": s.doctor_id,
        "day_of_week": s.day_of_week,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "is_active": bool(s.is_active),
        "created_at": s.created_at,
    }


def _fmt_config(c: DoctorSlotConfig) -> dict:
    return {
        "config_id": c.config_id,
        "doctor_id": c.doctor_id,
        "slot_duration_minutes": c.slot_duration_minutes,
        "updated_at": c.updated_at,
    }


def _fmt_block(b: DoctorAvailabilityBlock) -> dict:
    return {
        "block_id": b.block_id,
        "doctor_id": b.doctor_id,
        "block_date": b.block_date,
        "start_time": b.start_time,
        "end_time": b.end_time,
        "reason": b.reason,
        "created_at": b.created_at,
    }


# --- Schedule ---

class ScheduleCreateRequest(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str


class ScheduleUpdateRequest(BaseModel):
    start_time: str | None = None
    end_time: str | None = None
    is_active: bool | None = None


@doctor_avail_router.get("/schedule")
def get_my_schedule(
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    schedules = (
        db.query(DoctorAvailabilitySchedule)
        .filter(DoctorAvailabilitySchedule.doctor_id == doctor.doctor_id)
        .all()
    )
    return {"items": [_fmt_schedule(s) for s in schedules]}


@doctor_avail_router.post("/schedule", status_code=201)
def create_schedule_window(
    payload: ScheduleCreateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    _validate_time_window(payload.day_of_week, payload.start_time, payload.end_time)
    window = DoctorAvailabilitySchedule(
        doctor_id=doctor.doctor_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(window)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="A window with this day and start time already exists")
    db.refresh(window)
    return _fmt_schedule(window)


@doctor_avail_router.put("/schedule/{schedule_id}")
def update_schedule_window(
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    s = db.get(DoctorAvailabilitySchedule, schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Schedule window not found")
    if s.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=403, detail="Not your schedule window")
    if payload.start_time is not None:
        s.start_time = payload.start_time
    if payload.end_time is not None:
        s.end_time = payload.end_time
    if payload.is_active is not None:
        s.is_active = 1 if payload.is_active else 0
    db.commit()
    db.refresh(s)
    return _fmt_schedule(s)


@doctor_avail_router.delete("/schedule/{schedule_id}", status_code=204)
def delete_schedule_window(
    schedule_id: int,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    s = db.get(DoctorAvailabilitySchedule, schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Schedule window not found")
    if s.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=403, detail="Not your schedule window")
    db.delete(s)
    db.commit()


# --- Config ---

class ConfigUpdateRequest(BaseModel):
    slot_duration_minutes: int


@doctor_avail_router.get("/config")
def get_my_config(
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    config = (
        db.query(DoctorSlotConfig)
        .filter(DoctorSlotConfig.doctor_id == doctor.doctor_id)
        .first()
    )
    if config is None:
        return {"config_id": None, "doctor_id": doctor.doctor_id, "slot_duration_minutes": 30, "updated_at": None}
    return _fmt_config(config)


@doctor_avail_router.put("/config")
def update_my_config(
    payload: ConfigUpdateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    _validate_slot_duration(payload.slot_duration_minutes)
    config = (
        db.query(DoctorSlotConfig)
        .filter(DoctorSlotConfig.doctor_id == doctor.doctor_id)
        .first()
    )
    if config is None:
        config = DoctorSlotConfig(
            doctor_id=doctor.doctor_id,
            slot_duration_minutes=payload.slot_duration_minutes,
            updated_at=now_iso(),
        )
        db.add(config)
    else:
        config.slot_duration_minutes = payload.slot_duration_minutes
        config.updated_at = now_iso()
    db.commit()
    db.refresh(config)
    return _fmt_config(config)


# --- Blocks ---

class BlockCreateRequest(BaseModel):
    block_date: str
    start_time: str | None = None
    end_time: str | None = None
    reason: str | None = None


@doctor_avail_router.get("/blocks")
def get_my_blocks(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    q = db.query(DoctorAvailabilityBlock).filter(
        DoctorAvailabilityBlock.doctor_id == doctor.doctor_id
    )
    if from_date:
        q = q.filter(DoctorAvailabilityBlock.block_date >= from_date)
    if to_date:
        q = q.filter(DoctorAvailabilityBlock.block_date <= to_date)
    return {"items": [_fmt_block(b) for b in q.order_by(DoctorAvailabilityBlock.block_date).all()]}


@doctor_avail_router.post("/blocks", status_code=201)
def create_block(
    payload: BlockCreateRequest,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    _validate_block(payload.start_time, payload.end_time)
    block = DoctorAvailabilityBlock(
        doctor_id=doctor.doctor_id,
        block_date=payload.block_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        reason=payload.reason,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return _fmt_block(block)


@doctor_avail_router.delete("/blocks/{block_id}", status_code=204)
def delete_block(
    block_id: int,
    current_user: User = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
):
    doctor = _get_doctor_profile(db, current_user)
    b = db.get(DoctorAvailabilityBlock, block_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Block not found")
    if b.doctor_id != doctor.doctor_id:
        raise HTTPException(status_code=403, detail="Not your block")
    db.delete(b)
    db.commit()


# ---------------------------------------------------------------------------
# Admin-scoped router (/admin/doctors/{doctor_id}/availability/*)
# ---------------------------------------------------------------------------

admin_avail_router = APIRouter(
    prefix="/admin/doctors/{doctor_id}/availability",
    tags=["availability"],
)


def _get_doctor_or_404(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@admin_avail_router.get("/schedule")
def admin_get_schedule(
    doctor_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    schedules = (
        db.query(DoctorAvailabilitySchedule)
        .filter(DoctorAvailabilitySchedule.doctor_id == doctor_id)
        .all()
    )
    return {"items": [_fmt_schedule(s) for s in schedules]}


@admin_avail_router.post("/schedule", status_code=201)
def admin_create_schedule_window(
    doctor_id: int,
    payload: ScheduleCreateRequest,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    _validate_time_window(payload.day_of_week, payload.start_time, payload.end_time)
    window = DoctorAvailabilitySchedule(
        doctor_id=doctor_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(window)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="A window with this day and start time already exists")
    db.refresh(window)
    return _fmt_schedule(window)


@admin_avail_router.put("/schedule/{schedule_id}")
def admin_update_schedule_window(
    doctor_id: int,
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    s = db.get(DoctorAvailabilitySchedule, schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Schedule window not found")
    if s.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Schedule does not belong to this doctor")
    if payload.start_time is not None:
        s.start_time = payload.start_time
    if payload.end_time is not None:
        s.end_time = payload.end_time
    if payload.is_active is not None:
        s.is_active = 1 if payload.is_active else 0
    db.commit()
    db.refresh(s)
    return _fmt_schedule(s)


@admin_avail_router.delete("/schedule/{schedule_id}", status_code=204)
def admin_delete_schedule_window(
    doctor_id: int,
    schedule_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    s = db.get(DoctorAvailabilitySchedule, schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Schedule window not found")
    if s.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Schedule does not belong to this doctor")
    db.delete(s)
    db.commit()


@admin_avail_router.get("/config")
def admin_get_config(
    doctor_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    config = (
        db.query(DoctorSlotConfig)
        .filter(DoctorSlotConfig.doctor_id == doctor_id)
        .first()
    )
    if config is None:
        return {"config_id": None, "doctor_id": doctor_id, "slot_duration_minutes": 30, "updated_at": None}
    return _fmt_config(config)


@admin_avail_router.put("/config")
def admin_update_config(
    doctor_id: int,
    payload: ConfigUpdateRequest,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    _validate_slot_duration(payload.slot_duration_minutes)
    config = (
        db.query(DoctorSlotConfig)
        .filter(DoctorSlotConfig.doctor_id == doctor_id)
        .first()
    )
    if config is None:
        config = DoctorSlotConfig(
            doctor_id=doctor_id,
            slot_duration_minutes=payload.slot_duration_minutes,
            updated_at=now_iso(),
        )
        db.add(config)
    else:
        config.slot_duration_minutes = payload.slot_duration_minutes
        config.updated_at = now_iso()
    db.commit()
    db.refresh(config)
    return _fmt_config(config)


@admin_avail_router.get("/blocks")
def admin_get_blocks(
    doctor_id: int,
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    q = db.query(DoctorAvailabilityBlock).filter(
        DoctorAvailabilityBlock.doctor_id == doctor_id
    )
    if from_date:
        q = q.filter(DoctorAvailabilityBlock.block_date >= from_date)
    if to_date:
        q = q.filter(DoctorAvailabilityBlock.block_date <= to_date)
    return {"items": [_fmt_block(b) for b in q.order_by(DoctorAvailabilityBlock.block_date).all()]}


@admin_avail_router.post("/blocks", status_code=201)
def admin_create_block(
    doctor_id: int,
    payload: BlockCreateRequest,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    _validate_block(payload.start_time, payload.end_time)
    block = DoctorAvailabilityBlock(
        doctor_id=doctor_id,
        block_date=payload.block_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        reason=payload.reason,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return _fmt_block(block)


@admin_avail_router.delete("/blocks/{block_id}", status_code=204)
def admin_delete_block(
    doctor_id: int,
    block_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    _get_doctor_or_404(db, doctor_id)
    b = db.get(DoctorAvailabilityBlock, block_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Block not found")
    if b.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Block does not belong to this doctor")
    db.delete(b)
    db.commit()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_time_window(day_of_week: int, start_time: str, end_time: str) -> None:
    if day_of_week not in range(7):
        raise HTTPException(status_code=400, detail="day_of_week must be 0 (Monday) through 6 (Sunday)")
    try:
        s = datetime.strptime(start_time, "%H:%M")
        e = datetime.strptime(end_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="start_time and end_time must be HH:MM format")
    if s >= e:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")


def _validate_slot_duration(minutes: int) -> None:
    if minutes not in {10, 15, 20, 30, 45, 60}:
        raise HTTPException(status_code=400, detail="slot_duration_minutes must be one of: 10, 15, 20, 30, 45, 60")


def _validate_block(start_time: str | None, end_time: str | None) -> None:
    # Both must be null (full-day) or both non-null (time-range)
    if (start_time is None) != (end_time is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both start_time and end_time for a partial block, or neither for a full-day block",
        )
