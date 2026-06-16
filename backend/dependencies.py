"""Reusable FastAPI dependencies for authenticated requests."""

import uuid

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
    if user is None or not user.is_active:
        raise _credentials_error
    return user
