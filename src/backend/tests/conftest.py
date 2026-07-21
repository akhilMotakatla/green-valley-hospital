"""Shared test fixtures for Green Valley Hospital backend tests.

Uses an in-memory SQLite database per test function. The FastAPI `get_db`
dependency is overridden so every HTTP call goes through the same test
session as the setup code — no data isolation surprises.

TestClient is created WITHOUT using it as a context manager so FastAPI's
startup/shutdown lifecycle events (init_db, StaticFiles mount) do not fire
during tests. The test engine and its in-memory DB are self-contained.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Appointment,
    Department,
    Doctor,
    DoctorAvailabilityBlock,
    DoctorAvailabilitySchedule,
    DoctorSlotConfig,
    IntakeForm,
    Invoice,
    LabOrder,
    LabResult,
    LabTechnician,
    Notification,
    NotificationSchedule,
    Patient,
    StaffMember,
    User,
)
from app.security import create_access_token, hash_password

# ---------------------------------------------------------------------------
# Test engine — in-memory SQLite, isolated per test session.
# ---------------------------------------------------------------------------

_TEST_DB_URL = "sqlite:///:memory:"
# StaticPool forces SQLAlchemy to reuse a single connection so all sessions
# share the same in-memory SQLite database. Without this, each new connection
# gets a fresh empty database and "no such table" errors occur.
_test_engine = create_engine(
    _TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@sa_event.listens_for(_test_engine, "connect")
def _set_fk_pragma(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.close()


_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db() -> Session:
    """Create all tables, yield a fresh session, then drop everything."""
    Base.metadata.create_all(bind=_test_engine)
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """FastAPI TestClient with get_db overridden to use the test session."""

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    # Do NOT use as context manager — avoids triggering FastAPI startup events
    # (init_db writes to the production SQLite file; StaticFiles mount is
    # non-idempotent across multiple test fixture setups).
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------


def auth_headers(user: User) -> dict:
    """Return Bearer auth headers for the given user."""
    token, _ = create_access_token(
        user_id=user.id,
        role=user.role,
        email=user.email,
        full_name=user.full_name,
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Shared seed fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def dept(db: Session) -> Department:
    d = Department(name="Cardiology", description="Heart care", is_active=1)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@pytest.fixture()
def doctor_user(db: Session) -> User:
    u = User(
        email="dr.smith@hospital.test",
        password_hash=hash_password("Pass1234"),
        role="Doctor",
        full_name="Dr. Alice Smith",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def doctor_profile(db: Session, doctor_user: User, dept: Department) -> Doctor:
    d = Doctor(
        user_id=doctor_user.id,
        department_id=dept.department_id,
        specialty="Cardiology",
        years_experience=10,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@pytest.fixture()
def patient_user(db: Session) -> User:
    u = User(
        email="patient.one@test.com",
        password_hash=hash_password("Pass1234"),
        role="Patient",
        full_name="Patient One",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def patient_profile(db: Session, patient_user: User) -> Patient:
    p = Patient(user_id=patient_user.id, date_of_birth="1990-01-01", gender="F")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def patient2_user(db: Session) -> User:
    u = User(
        email="patient.two@test.com",
        password_hash=hash_password("Pass1234"),
        role="Patient",
        full_name="Patient Two",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def patient2_profile(db: Session, patient2_user: User) -> Patient:
    p = Patient(user_id=patient2_user.id, date_of_birth="1985-05-15", gender="M")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def admin_user(db: Session) -> User:
    u = User(
        email="admin@hospital.test",
        password_hash=hash_password("Pass1234"),
        role="Admin",
        full_name="Admin User",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def staff_user(db: Session) -> User:
    u = User(
        email="staff@hospital.test",
        password_hash=hash_password("Pass1234"),
        role="Staff",
        full_name="Staff User",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def staff_member(db: Session, staff_user: User, dept: Department) -> StaffMember:
    s = StaffMember(user_id=staff_user.id, department_id=dept.department_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def lab_user(db: Session) -> User:
    u = User(
        email="lab@hospital.test",
        password_hash=hash_password("Pass1234"),
        role="Lab",
        full_name="Lab Tech",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def lab_tech(db: Session, lab_user: User) -> LabTechnician:
    lt = LabTechnician(user_id=lab_user.id)
    db.add(lt)
    db.commit()
    db.refresh(lt)
    return lt


# ---------------------------------------------------------------------------
# Convenience: Monday schedule (9:00-12:00, 30-min slots, day_of_week=0)
# 2026-07-27 is a Monday — verified: datetime(2026,7,27).weekday() == 0
# ---------------------------------------------------------------------------

TEST_MONDAY = "2026-07-27"


@pytest.fixture()
def monday_schedule(db: Session, doctor_profile: Doctor) -> DoctorAvailabilitySchedule:
    """Week schedule: Monday 09:00-12:00 (produces 6 x 30-min slots)."""
    s = DoctorAvailabilitySchedule(
        doctor_id=doctor_profile.doctor_id,
        day_of_week=0,  # Monday
        start_time="09:00",
        end_time="12:00",
        is_active=1,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s
