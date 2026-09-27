"""Facilities router — CRUD for monitored sites."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_role
from models.facility import Facility
from models.user import User
from schemas.facility import FacilityCreate, FacilityResponse, FacilityUpdate

router = APIRouter()


@router.get("", response_model=list[FacilityResponse])
def list_facilities(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Facility]:
    query = db.query(Facility).order_by(Facility.created_at)
    if user.role.name != "admin":
        query = query.filter(Facility.id == user.facility_id)
    return query.all()


@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(
    facility_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Facility:
    """Get a single facility by ID."""
    from uuid import UUID
    facility = db.get(Facility, UUID(facility_id))
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    if user.role.name != "admin" and facility.id != user.facility_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this facility")
    return facility


@router.post("", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> Facility:
    facility = Facility(
        name=payload.name,
        location=payload.location,
        region_code=payload.region_code,
        facility_type=payload.facility_type,
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)

    # Auto-assign facility to the creating facility_manager so they can use it
    if user.role.name == "facility_manager":
        user.facility_id = facility.id
        db.commit()
    elif user.role.name == "admin" and user.facility_id is None:
        # Admin without a facility gets assigned too
        user.facility_id = facility.id
        db.commit()

    return facility


@router.patch("/{facility_id}", response_model=FacilityResponse)
def update_facility(
    facility_id: str,
    payload: FacilityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> Facility:
    """Update a facility (admin only)."""
    from uuid import UUID
    facility = db.get(Facility, UUID(facility_id))
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

    if payload.name is not None:
        facility.name = payload.name
    if payload.location is not None:
        facility.location = payload.location
    if payload.region_code is not None:
        facility.region_code = payload.region_code
    if payload.facility_type is not None:
        facility.facility_type = payload.facility_type

    db.commit()
    db.refresh(facility)
    return facility


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_facility(
    facility_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> None:
    """Delete a facility (admin only)."""
    from uuid import UUID
    facility = db.get(Facility, UUID(facility_id))
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    db.delete(facility)
    db.commit()
