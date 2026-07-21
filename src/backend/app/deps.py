from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import JWTError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes/validates the JWT, loads the user. 401 if missing/expired/invalid
    (AUTH-4).
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user


def require_role(*roles: str):
    """Dependency factory that 403s if current_user.role isn't in the allowed
    set. Row-level ownership checks happen separately, inside each endpoint.
    """

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this action")
        return current_user

    return _checker


def require_billing_specialist(current_user: User = Depends(get_current_user)) -> User:
    """Convenience dependency for BillingSpecialist-only routes (AUTHZ-10).
    Also accepted by Admin on notification log endpoints (Section 9.6).
    This is a plain dependency (not a factory) because the billing router uses
    it as a default dependency on all routes; endpoints that also allow Admin
    supply their own override dependency inline.
    """
    if current_user.role != "BillingSpecialist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this action"
        )
    return current_user
