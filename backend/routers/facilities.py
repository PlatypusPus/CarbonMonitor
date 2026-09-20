"""Facilities router — CRUD for monitored sites."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.facility import Facility
from schemas.facility import FacilityCreate, FacilityResponse

router = APIRouter()


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(facility: FacilityCreate, db: Session = Depends(get_db)) -> Any:
    db_facility = Facility(**facility.model_dump())
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility


@router.get("/", response_model=list[FacilityResponse])
def list_facilities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> Any:
    stmt = select(Facility).offset(skip).limit(limit)
    facilities = db.execute(stmt).scalars().all()
    return facilities


@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(facility_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    facility = db.get(Facility, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


@router.patch("/{facility_id}", response_model=FacilityResponse)
def update_facility(facility_id: uuid.UUID, facility_update: FacilityCreate, db: Session = Depends(get_db)) -> Any:
    facility = db.get(Facility, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    for k, v in facility_update.model_dump(exclude_unset=True).items():
        setattr(facility, k, v)
    db.commit()
    db.refresh(facility)
    return facility
