"""Refresh-token session lifecycle: issue, rotate, and revoke."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from config import get_settings
from models.session import UserSession
from models.user import User
from security import generate_refresh_token, hash_refresh_token


def _expiry() -> datetime:
    days = get_settings().refresh_token_expire_days
    return datetime.now(timezone.utc) + timedelta(days=days)


def _add_session(db: Session, user_id: uuid.UUID) -> str:
    raw_token = generate_refresh_token()
    db.add(
        UserSession(
            user_id=user_id,
            refresh_token_hash=hash_refresh_token(raw_token),
            expires_at=_expiry(),
        )
    )
    return raw_token


def _active_session(db: Session, raw_token: str) -> UserSession | None:
    session = (
        db.query(UserSession)
        .filter(UserSession.refresh_token_hash == hash_refresh_token(raw_token))
        .first()
    )
    if session is None or session.revoked:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    return session


def issue_refresh_token(db: Session, user_id: uuid.UUID) -> str:
    raw_token = _add_session(db, user_id)
    db.commit()
    return raw_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str] | None:
    session = _active_session(db, raw_token)
    if session is None:
        return None
    session.revoked = True
    user = db.get(User, session.user_id)
    new_token = _add_session(db, session.user_id)
    db.commit()
    return user, new_token


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    session = _active_session(db, raw_token)
    if session is not None:
        session.revoked = True
        db.commit()
