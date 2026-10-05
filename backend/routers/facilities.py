"""Facilities router — CRUD for monitored sites."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_role, check_facility_access
from models.activity_record import ActivityRecord
from models.facility import Facility
from models.ocr_draft import OCRDraft
from models.user import User
from schemas.facility import FacilityCreate, FacilityResponse, FacilityUpdate

router = APIRouter()


@router.get("", response_model=list[FacilityResponse])
def list_facilities(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Facility]:
    query = db.query(Facility).filter(Facility.organization_id == user.organization_id).order_by(Facility.created_at)
    if user.role.name != "admin":
        query = query.filter(Facility.id == user.facility_id)
    return query.all()


@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(
    facility_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Facility:
    """Get a single facility by ID."""
    facility = db.get(Facility, facility_id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    check_facility_access(user, facility.id)
    return facility


@router.post("", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> Facility:
    facility = Facility(
        organization_id=user.organization_id,
        name=payload.name,
        location=payload.location,
        region_code=payload.region_code,
        facility_type=payload.facility_type,
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)

    return facility


@router.patch("/{facility_id}", response_model=FacilityResponse)
def update_facility(
    facility_id: UUID,
    payload: FacilityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> Facility:
    """Managers can edit their own facility's details."""
    check_facility_access(user, facility_id)
    facility = db.get(Facility, facility_id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is None:
        raise HTTPException(422, "Facility name cannot be null")
    for key, value in changes.items():
        setattr(facility, key, value)

    db.commit()
    db.refresh(facility)
    return facility


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_facility(
    facility_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> None:
    """Delete a facility (admin only)."""
    check_facility_access(user, facility_id)
    facility = db.get(Facility, facility_id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    in_use = (
        db.query(User.id).filter(User.facility_id == facility_id).first()
        or db.query(ActivityRecord.id).filter(ActivityRecord.facility_id == facility_id).first()
        or db.query(OCRDraft.id).filter(OCRDraft.facility_id == facility_id).first()
    )
    conflict = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This facility still has users or records. Reassign or remove them first.",
    )
    if in_use:
        raise conflict
    db.delete(facility)
    try:
        db.commit()
    except IntegrityError:  # some other table still references it
        db.rollback()
        raise conflict from None
