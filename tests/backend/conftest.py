from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `app` importable: src/backend is the package root for the FastAPI app.
BACKEND_ROOT = Path(__file__).resolve().parents[2] / "src" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Department, Doctor, User
from app.security import hash_password

# Separate, isolated in-memory SQLite DB per test session (never touches
# db/green_valley.db).
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def _fresh_db():
    """Create all tables before each test, drop them after -- fully isolated,
    no shared state leaking between tests.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers for seeding users of each role directly (bypassing HTTP, since
# non-Patient roles cannot be created via public signup per AUTH-3).
# ---------------------------------------------------------------------------


def make_user(db_session, *, email, role, full_name="Test User", password="Passw0rd!", is_active=True):
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        full_name=full_name,
        phone="555-0000",
        is_active=1 if is_active else 0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_department(db_session, name="Cardiology"):
    dept = Department(name=name, description="desc", is_active=1)
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


def make_doctor_user(db_session, *, email="doc@example.com", full_name="Dr. Test", department=None):
    if department is None:
        department = make_department(db_session, name=f"Dept-{email}")
    user = make_user(db_session, email=email, role="Doctor", full_name=full_name)
    doctor = Doctor(
        user_id=user.id,
        department_id=department.department_id,
        specialty="General",
        years_experience=5,
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return user, doctor


def login(client, email, password="Passw0rd!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
