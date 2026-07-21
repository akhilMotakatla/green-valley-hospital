from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def validate_password_policy(password: str) -> bool:
    """SEC-1: min 8 chars, at least one letter and one number."""
    return bool(_PASSWORD_RE.match(password))


def create_access_token(*, user_id: int, role: str, email: str, full_name: str) -> tuple[str, int]:
    """Returns (token, expires_in_seconds).

    JWT payload (v1.2 / AC-JWT-FIELDS): sub, role, email, full_name, exp.
    The frontend AuthContext reads email and full_name directly from the
    decoded token — no additional /auth/me call is needed for sidebar display.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "full_name": full_name,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def decode_access_token(token: str) -> dict:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


__all__ = [
    "hash_password",
    "verify_password",
    "validate_password_policy",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]
