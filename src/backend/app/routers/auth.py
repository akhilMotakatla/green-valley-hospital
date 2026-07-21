from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Patient, User
from app.schemas import LoginRequest, SignupRequest
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    # AC-AUTH-1: role is always forced to "Patient" — the request schema has
    # no `role` field at all, closing the injection path entirely.
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="Patient",
        full_name=payload.full_name,
        phone=payload.phone,
        is_active=1,
    )
    db.add(user)
    db.flush()

    patient = Patient(user_id=user.id, date_of_birth=payload.date_of_birth)
    db.add(patient)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": bool(user.is_active),
        "created_at": user.created_at,
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # AUTH-5: generic error, never reveals whether the email exists.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    token, expires_in = create_access_token(
        user_id=user.id, role=user.role, email=user.email, full_name=user.full_name
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "role": user.role,
        "user_id": user.id,
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "is_active": bool(current_user.is_active),
        "created_at": current_user.created_at,
    }
