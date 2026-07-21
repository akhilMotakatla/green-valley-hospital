"""Availability service — slot computation for REQ-01.

get_available_slots() is a pure function (testable in isolation). It
generates all candidate time slots from a doctor's weekly schedule for a
given date, then removes blocked, booked, and waitlist-held slots.

Algorithm per docs/technical-design.md §4.2 endpoint 11.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    DoctorAvailabilityBlock,
    DoctorAvailabilitySchedule,
    DoctorSlotConfig,
    WaitlistEntry,
)

_ALLOWED_DURATIONS = {10, 15, 20, 30, 45, 60}
_DEFAULT_DURATION = 30


def get_available_slots(db: Session, doctor_id: int, date_str: str) -> list[str]:
    """Return sorted list of available HH:MM slot strings for doctor on date_str.

    Steps:
      1. Load weekly schedule windows for the day-of-week.
      2. Resolve slot duration from doctor_slot_configs (default 30 min).
      3. Generate all candidate slots from windows.
      4. Remove slots covered by one-off blocks (full-day or time-range).
      5. Remove already-booked slots (status in Scheduled/Completed).
      6. Remove waitlist-held slots (status='Notified' for doctor+date).
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return []

    dow = date_obj.weekday()  # 0=Monday, 6=Sunday

    # 1. Weekly schedule windows for this day
    windows = (
        db.query(DoctorAvailabilitySchedule)
        .filter(
            DoctorAvailabilitySchedule.doctor_id == doctor_id,
            DoctorAvailabilitySchedule.day_of_week == dow,
            DoctorAvailabilitySchedule.is_active == 1,
        )
        .all()
    )
    if not windows:
        return []

    # 2. Slot duration
    config = (
        db.query(DoctorSlotConfig)
        .filter(DoctorSlotConfig.doctor_id == doctor_id)
        .first()
    )
    slot_minutes = config.slot_duration_minutes if config else _DEFAULT_DURATION

    # 3. Generate candidate slots
    candidates: list[str] = []
    for w in windows:
        try:
            t = datetime.strptime(f"{date_str}T{w.start_time}", "%Y-%m-%dT%H:%M")
            end = datetime.strptime(f"{date_str}T{w.end_time}", "%Y-%m-%dT%H:%M")
        except ValueError:
            continue
        delta = timedelta(minutes=slot_minutes)
        while t + delta <= end:
            candidates.append(t.strftime("%H:%M"))
            t += delta

    if not candidates:
        return []

    # 4. Remove blocked slots
    blocks = (
        db.query(DoctorAvailabilityBlock)
        .filter(
            DoctorAvailabilityBlock.doctor_id == doctor_id,
            DoctorAvailabilityBlock.block_date == date_str,
        )
        .all()
    )
    for block in blocks:
        if block.start_time is None:
            # Full-day block — nothing available
            return []
        try:
            b_start = datetime.strptime(block.start_time, "%H:%M")
            b_end = datetime.strptime(block.end_time, "%H:%M")
        except (ValueError, TypeError):
            continue
        candidates = [
            s for s in candidates
            if not (
                datetime.strptime(s, "%H:%M") >= b_start
                and datetime.strptime(s, "%H:%M") < b_end
            )
        ]

    if not candidates:
        return []

    # 5. Remove already-booked slots
    booked_rows = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_(["Scheduled", "Completed"]),
        )
        .all()
    )
    booked_times: set[str] = set()
    for appt in booked_rows:
        try:
            appt_dt = datetime.fromisoformat(appt.scheduled_at.replace("Z", "+00:00"))
            if appt_dt.strftime("%Y-%m-%d") == date_str:
                booked_times.add(appt_dt.strftime("%H:%M"))
        except (ValueError, AttributeError):
            continue
    candidates = [s for s in candidates if s not in booked_times]

    if not candidates:
        return []

    # 6. Remove waitlist-held slots
    held_rows = (
        db.query(WaitlistEntry)
        .filter(
            WaitlistEntry.doctor_id == doctor_id,
            WaitlistEntry.preferred_date == date_str,
            WaitlistEntry.status == "Notified",
            WaitlistEntry.held_slot_time.isnot(None),
        )
        .all()
    )
    held_times = {row.held_slot_time for row in held_rows}
    candidates = [s for s in candidates if s not in held_times]

    return sorted(candidates)
