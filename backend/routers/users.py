"""Administrator-managed accounts; facility membership is never self-assigned."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.facility import Facility
from models.role import Role
from models.session import UserSession
from models.user import User
from routers.auth import me
from schemas.user import UserCreate, UserUpdate, UserResponse
from security import hash_password

router = APIRouter()


def validate_membership(db, role_name, facility_id):
    if role_name != "admin" and facility_id is None:
        raise HTTPException(422, "A facility manager must be assigned to a facility")
    if facility_id is not None and db.get(Facility, facility_id) is None:
        raise HTTPException(422, "Facility not found")
    role = db.query(Role).filter(Role.name == role_name).one_or_none()
    if role is None:
        raise HTTPException(422, "Role not available")
    return role


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_role("admin"))):
    return [me(user) for user in db.query(User).filter(User.organization_id == admin.organization_id).order_by(User.created_at).all()]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db),
                admin: User = Depends(require_role("admin"))):
    email = str(payload.email).strip().lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(409, "An account with this email already exists")
    facility_id = payload.facility_id
    if payload.role == "facility_manager" and facility_id is None:
        facility = Facility(name=f"{payload.full_name}'s facility", organization_id=admin.organization_id)
        db.add(facility)
        db.flush()
        facility_id = facility.id
    elif facility_id is not None:
        from dependencies import check_facility_access
        check_facility_access(admin, facility_id)
    role = validate_membership(db, payload.role, facility_id)
    user = User(email=email, full_name=payload.full_name, hashed_password=hash_password(payload.password),
                role_id=role.id, facility_id=facility_id, organization_id=admin.organization_id, is_active=True)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists") from None
    db.refresh(user)
    return me(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, payload: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_role("admin"))):
    user = db.get(User, user_id)
    if user is None or user.organization_id != admin.organization_id:
        raise HTTPException(404, "User not found")
    changes = payload.model_dump(exclude_unset=True)
    if any(changes.get(key, True) is None for key in ("role", "is_active", "full_name")):
        raise HTTPException(422, "Name, role and active status cannot be null")
    if "full_name" in changes and not changes["full_name"].strip():
        raise HTTPException(422, "Name is required")
    role_name = changes.get("role", user.role.name)
    if user.id == admin.id and (role_name != "admin" or changes.get("is_active") is False):
        raise HTTPException(409, "You cannot disable or demote your own administrator account")
    facility_id = changes.get("facility_id", user.facility_id)
    if facility_id is not None:
        from dependencies import check_facility_access
        check_facility_access(admin, facility_id)
    role = validate_membership(db, role_name, facility_id)
    user.role = role
    user.facility_id = facility_id
    if "full_name" in changes:
        user.full_name = changes["full_name"].strip()
    if "is_active" in changes:
        user.is_active = changes["is_active"]
    if {"role", "facility_id", "is_active"} & changes.keys():
        user.auth_version += 1
        db.query(UserSession).filter(UserSession.user_id == user.id).update({"revoked": True})
    db.commit()
    db.refresh(user)
    return me(user)
