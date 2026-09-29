"""Reusable FastAPI dependencies for authenticated requests."""

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from security import decode_token

_bearer_scheme = HTTPBearer(auto_error=False)
_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _credentials_error
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise _credentials_error from None
    if payload.get("type") != "access":
        raise _credentials_error
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _credentials_error from None

    user = db.get(User, user_id)
    if user is None or not user.is_active or not user.email_verified or payload.get("version", 0) != user.auth_version:
        raise _credentials_error
    from models.facility import Facility
    user.allowed_facility_ids = [row[0] for row in db.query(Facility.id).filter(Facility.organization_id == user.organization_id).all()]
    return user


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker

def check_facility_access(user: User, facility_id: uuid.UUID) -> None:
    allowed = getattr(user, "allowed_facility_ids", None)
    if allowed is not None and facility_id not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized to access this facility")
    if user.role.name != "admin" and (user.facility_id is None or user.facility_id != facility_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this facility",
        )


def facility_scope(
    facility_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
) -> uuid.UUID | list[uuid.UUID]:
    """Admins receive their organization's facility IDs; managers get one facility."""
    if user.role.name == "admin":
        if facility_id is not None:
            check_facility_access(user, facility_id)
            return facility_id
        return getattr(user, "allowed_facility_ids", [])
    if user.facility_id is None:
        raise HTTPException(status_code=403, detail="Ask an administrator to assign your facility")
    if facility_id is not None:
        check_facility_access(user, facility_id)
    return user.facility_id
