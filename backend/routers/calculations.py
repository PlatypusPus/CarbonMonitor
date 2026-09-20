"""Calculations router — trigger emission calculation for activity records."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, check_facility_access
from models.user import User
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from schemas.calculated_emission import CalculatedEmissionResponse
from services.calculation import calculate_emissions

router = APIRouter()


@router.post("/{activity_record_id}/calculate", response_model=CalculatedEmissionResponse)
def calculate_record(
    activity_record_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    record = db.get(ActivityRecord, activity_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="ActivityRecord not found")
    check_facility_access(current_user, record.facility_id)
    
    from models.facility import Facility
    facility = db.get(Facility, record.facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    stmt = select(EmissionFactor).where(
        EmissionFactor.activity_type == record.activity_type,
        or_(EmissionFactor.region == facility.region_code, EmissionFactor.region.is_(None)),
        or_(EmissionFactor.valid_from <= record.period_end, EmissionFactor.valid_from.is_(None)),
        or_(EmissionFactor.valid_to >= record.period_end, EmissionFactor.valid_to.is_(None))
    ).limit(1)
    factor = db.execute(stmt).scalar_one_or_none()
    if not factor:
        raise HTTPException(
            status_code=400, 
            detail=f"No emission factor found for activity type: {record.activity_type}"
        )
    
    calc = calculate_emissions(record, factor)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    
    return calc


@router.get("/", response_model=list[CalculatedEmissionResponse])
def list_calculations(
    skip: int = 0, limit: int = 100, activity_record_id: uuid.UUID | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    stmt = select(CalculatedEmission).offset(skip).limit(limit)
    
    # Restrict to user's facility if not admin
    if current_user.role.name != "admin":
        stmt = stmt.join(ActivityRecord).where(ActivityRecord.facility_id == current_user.facility_id)
        
    if activity_record_id:
        if current_user.role.name != "admin":
            # Just to double check they aren't requesting an ID outside their facility
            record = db.get(ActivityRecord, activity_record_id)
            if record:
                check_facility_access(current_user, record.facility_id)
        stmt = stmt.where(CalculatedEmission.activity_record_id == activity_record_id)
        
    results = db.execute(stmt).scalars().all()
    return results
