"""Verified signup, self-service account settings and email-bound invitations."""
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from config import get_settings
from database import get_db
from dependencies import get_current_user, require_role, check_facility_access
from models.organization import Organization, EmailToken
from models.user import User
from models.role import Role
from models.facility import Facility
from models.activity_record import ActivityRecord
from models.upload import Upload
from models.session import UserSession
from routers.auth import me, REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from security import hash_password, verify_password, hash_refresh_token
from services.mailer import send_account_email

router = APIRouter()


class Signup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    organization_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10, max_length=72)

    @field_validator("full_name", "organization_name")
    @classmethod
    def required_name(cls, value):
        if not value.strip():
            raise ValueError("Name is required")
        return value.strip()

    @field_validator("password")
    @classmethod
    def password_length(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class EmailRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=40, max_length=200)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    full_name: str = Field(min_length=1, max_length=255)


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: str = Field(min_length=10, max_length=72)
    _validate_password = field_validator("new_password")(Signup.password_length.__func__)


class DeleteAccount(BaseModel):
    password: str = Field(max_length=72)
    confirmation: str


class Invitation(EmailRequest):
    facility_id: UUID


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def throttle(db, requester):
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    if db.query(EmailToken).filter(EmailToken.requester == requester, EmailToken.created_at > since).count() >= 10:
        raise HTTPException(429, "Too many email requests. Try again in an hour.")


def issue_link(db, *, purpose, email, requester, user_id=None, organization_id=None, facility_id=None):
    throttle(db, requester)
    now = datetime.now(timezone.utc)
    recent = db.query(EmailToken).filter(EmailToken.email == email, EmailToken.purpose == purpose,
        EmailToken.created_at > now - timedelta(seconds=60)).first()
    if recent:
        raise HTTPException(429, "Wait a minute before requesting another email.")
    raw = secrets.token_urlsafe(48)
    db.add(EmailToken(token_hash=hash_refresh_token(raw), purpose=purpose, email=email,
        requester=requester, user_id=user_id, organization_id=organization_id, facility_id=facility_id,
        expires_at=now + timedelta(hours=24 if purpose == "verify" else 168)))
    route = "verify-email" if purpose == "verify" else "join-organization"
    url = get_settings().public_app_url.rstrip('/') + f"/{route}#token={raw}"
    subject = "Verify your CarbonTrace email" if purpose == "verify" else "Join an organization on CarbonTrace"
    send_account_email(email, subject, f"{subject}\n\nOpen this link to continue:\n{url}\n\nThis link is single-use and expires in {'24 hours' if purpose == 'verify' else '7 days'}. If you did not request it, ignore this email.")


def find_token(db, raw, purpose):
    token = db.query(EmailToken).filter(EmailToken.token_hash == hash_refresh_token(raw), EmailToken.purpose == purpose).with_for_update().first()
    if not token or token.used_at or utc(token.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(400, "This link is invalid or expired. Request a new email.")
    return token


def revoke_sessions(db, user):
    user.auth_version += 1
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"revoked": True})


def protect_last_admin(db, user):
    if user.role.name != "admin":
        return
    # Serialize departure checks for this organization.
    if user.organization_id:
        db.query(Organization).filter(Organization.id == user.organization_id).with_for_update().first()
    others = db.query(User).join(Role).filter(User.organization_id == user.organization_id,
        User.id != user.id, User.is_active.is_(True), Role.name == "admin").count()
    has_members = db.query(User).filter(User.organization_id == user.organization_id, User.id != user.id, User.is_active.is_(True)).count()
    has_records = db.query(ActivityRecord).join(Facility).filter(Facility.organization_id == user.organization_id).first()
    if not others and (has_members or has_records):
        raise HTTPException(409, "Assign another administrator before leaving or deleting your account.")


@router.post('/signup', status_code=201)
def signup(payload: Signup, request: Request, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    requester = hash_refresh_token(request.client.host if request.client else 'unknown')
    throttle(db, requester)
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(409, "An account already exists. Sign in or resend verification.")
    organization = Organization(name=payload.organization_name)
    db.add(organization)
    db.flush()
    facility = Facility(name=f"{payload.organization_name} facility", organization_id=organization.id)
    db.add(facility)
    db.flush()
    role = db.query(Role).filter(Role.name == 'admin').one()
    user = User(email=email, full_name=payload.full_name, hashed_password=hash_password(payload.password),
        role=role, organization_id=organization.id, facility_id=facility.id, email_verified=False)
    db.add(user)
    try:
        db.flush()
        issue_link(db, purpose='verify', email=email, requester=requester, user_id=user.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account already exists. Sign in or resend verification.") from None
    return {'message': 'Check your email to verify your account before signing in.'}


@router.post('/resend-verification')
def resend(payload: EmailRequest, request: Request, db: Session = Depends(get_db)):
    requester = hash_refresh_token(request.client.host if request.client else 'unknown')
    throttle(db, requester)
    user = db.query(User).filter(func.lower(User.email) == str(payload.email).lower()).first()
    if user and user.is_active and not user.email_verified:
        issue_link(db, purpose='verify', email=user.email, requester=requester, user_id=user.id)
        db.commit()
    return {'message': 'If this account needs verification, a new email has been sent.'}


@router.post('/verify-email')
def verify(payload: TokenRequest, db: Session = Depends(get_db)):
    token = find_token(db, payload.token, 'verify')
    user = db.get(User, token.user_id)
    if not user or not user.is_active or user.email != token.email:
        raise HTTPException(400, 'This verification is no longer valid.')
    user.email_verified = True
    db.query(EmailToken).filter(EmailToken.user_id == user.id, EmailToken.purpose == 'verify').update({'used_at': datetime.now(timezone.utc)})
    db.commit()
    return {'message': 'Email verified. You can now sign in.'}


@router.get('/profile')
def profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {**me(user).model_dump(), 'uploads': db.query(Upload).filter(Upload.user_id == user.id).count(),
        'active_sessions': db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.revoked.is_(False), UserSession.expires_at > datetime.now(timezone.utc)).count()}


@router.patch('/profile')
def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.full_name = payload.full_name
    db.commit()
    return me(user)


@router.post('/password')
def change_password(payload: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(403, 'Current password is incorrect')
    user.hashed_password = hash_password(payload.new_password)
    revoke_sessions(db, user)
    db.commit()
    return {'message': 'Password changed. Sign in again.'}


@router.delete('/profile', status_code=204)
def delete_account(payload: DeleteAccount, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.confirmation != 'DELETE' or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(403, 'Enter your current password and DELETE to confirm')
    protect_last_admin(db, user)
    db.query(EmailToken).filter(EmailToken.user_id == user.id).delete()
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    user.email = f'deleted-{user.id}@deleted.example.com'
    user.full_name = 'Deleted account'
    user.hashed_password = hash_password(secrets.token_urlsafe(32))
    user.is_active = False
    user.email_verified = False
    user.last_login_at = None
    user.organization_id = None
    user.facility_id = None
    db.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.post('/invitations', status_code=201)
def invite(payload: Invitation, user: User = Depends(require_role('admin')), db: Session = Depends(get_db)):
    check_facility_access(user, payload.facility_id)
    issue_link(db, purpose='invite', email=str(payload.email).lower(), requester=str(user.id),
        user_id=user.id, organization_id=user.organization_id, facility_id=payload.facility_id)
    db.commit()
    return {'message': 'Invitation sent. It grants facility-manager access after acceptance.'}


def invited_facility(payload, user, db):
    token = find_token(db, payload.token, 'invite')
    if token.email != user.email:
        raise HTTPException(403, 'Sign in with the email address that received this invitation.')
    issuer = db.get(User, token.user_id)
    if not issuer or not issuer.is_active or issuer.role.name != 'admin' or issuer.organization_id != token.organization_id:
        raise HTTPException(400, 'This invitation is no longer available. Ask an administrator for a new one.')
    facility = db.get(Facility, token.facility_id)
    if not facility or facility.organization_id != token.organization_id:
        raise HTTPException(400, 'The invited facility is no longer available.')
    return token, facility


@router.post('/invitations/preview')
def preview_invitation(payload: TokenRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token, facility = invited_facility(payload, user, db)
    return {'organization': db.get(Organization, token.organization_id).name, 'facility': facility.name}


@router.post('/join')
def join(payload: TokenRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token, facility = invited_facility(payload, user, db)
    if user.organization_id != token.organization_id:
        protect_last_admin(db, user)
    elif user.role.name == 'admin':
        raise HTTPException(409, 'You are already an administrator of this organization.')
    user.organization_id = token.organization_id
    user.facility_id = token.facility_id
    user.role = db.query(Role).filter(Role.name == 'facility_manager').one()
    token.used_at = datetime.now(timezone.utc)
    revoke_sessions(db, user)
    db.commit()
    return {'message': 'Organization joined. Sign in again to open your new workspace.'}
