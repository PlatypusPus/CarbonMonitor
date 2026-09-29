"""Authentication endpoints: login, token refresh, logout."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from config import get_settings
from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.auth import LoginRequest, TokenResponse
from schemas.user import UserResponse
from security import create_access_token, verify_password
from services.sessions import issue_refresh_token, revoke_refresh_token, rotate_refresh_token

router = APIRouter()

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(func.lower(User.email) == str(payload.email).strip().lower()).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    if not user.email_verified:
        raise HTTPException(403, "Verify your email before signing in")
    user.last_login_at = datetime.now(timezone.utc)
    _set_refresh_cookie(response, issue_refresh_token(db, user.id))
    token = create_access_token(subject=str(user.id), role=user.role.name, version=user.auth_version)
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
) -> TokenResponse:
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    result = rotate_refresh_token(db, refresh_token)
    if result is None:
        response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user, new_token = result
    _set_refresh_cookie(response, new_token)
    token = create_access_token(subject=str(user.id), role=user.role.name, version=user.auth_version)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
) -> Response:
    if refresh_token is not None:
        revoke_refresh_token(db, refresh_token)
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.name,
        facility_id=current_user.facility_id,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        organization_id=current_user.organization_id,
        organization_name=current_user.organization.name if current_user.organization else None,
        email_verified=current_user.email_verified,
        last_login_at=current_user.last_login_at,
    )
