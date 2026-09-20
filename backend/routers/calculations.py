"""Calculations router — trigger emission calculation for activity records."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from schemas.calculated_emission import CalculatedEmissionResponse
from services.calculation import calculate_emissions

router = APIRouter()


@router.post("/{activity_record_id}/calculate", response_model=CalculatedEmissionResponse)
def calculate_record(activity_record_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    record = db.get(ActivityRecord, activity_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="ActivityRecord not found")
    
    stmt = select(EmissionFactor).where(EmissionFactor.activity_type == record.activity_type).limit(1)
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
    skip: int = 0, limit: int = 100, activity_record_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> Any:
    stmt = select(CalculatedEmission).offset(skip).limit(limit)
    if activity_record_id:
        stmt = stmt.where(CalculatedEmission.activity_record_id == activity_record_id)
    results = db.execute(stmt).scalars().all()
    return results
