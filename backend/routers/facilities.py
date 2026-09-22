"""Facilities router — CRUD for monitored sites."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_role
from models.facility import Facility
from models.user import User
from schemas.facility import FacilityCreate, FacilityResponse

router = APIRouter()


@router.get("", response_model=list[FacilityResponse])
def list_facilities(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Facility]:
    return db.query(Facility).order_by(Facility.created_at).all()


@router.post("", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "facility_manager")),
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
    return facility
