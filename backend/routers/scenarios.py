"""Scenarios router — what-if simulation endpoints."""

import uuid
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, check_facility_access
from models.user import User
from models.scenario import Scenario
from models.activity_record import ActivityRecord
from schemas.scenario import ScenarioCreate, ScenarioResponse, ScenarioPreview, ScenarioComparison
from services.scenario import run_scenario

router = APIRouter()


@router.post("/preview", response_model=ScenarioComparison)
def preview_scenario(payload: ScenarioPreview, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)) -> ScenarioComparison:
    """Compare a quantity change using the baseline's factor, without saving anything."""
    from models.calculated_emission import CalculatedEmission
    from models.emission_factor import EmissionFactor

    record = db.get(ActivityRecord, payload.activity_record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Activity record not found")
    check_facility_access(current_user, record.facility_id)
    if not record.confirmed_by_user:
        raise HTTPException(status_code=400, detail="Choose a confirmed activity record")
    emission = db.scalar(select(CalculatedEmission).where(
        CalculatedEmission.activity_record_id == record.id))
    if emission is None:
        raise HTTPException(status_code=400, detail="The baseline has no calculated emissions")
    factor = db.get(EmissionFactor, emission.emission_factor_id)
    if factor is None:
        raise HTTPException(status_code=400, detail="The baseline emission factor is missing")
    result = run_scenario(db, {
        "activity_type": record.activity_type, "quantity": record.quantity, "unit": record.unit,
    }, {"quantity": payload.quantity}, factor.region, record.period_end, factor=factor)
    projected = result["result_co2e_kg"]
    savings = emission.co2e_kg - projected
    return ScenarioComparison(
        activity_record_id=record.id, baseline_quantity=record.quantity,
        proposed_quantity=payload.quantity, unit=record.unit,
        baseline_co2e_kg=emission.co2e_kg, projected_co2e_kg=projected,
        savings_co2e_kg=savings,
        savings_percent=savings / emission.co2e_kg * 100 if emission.co2e_kg else None,
        factor_value=factor.factor_value, factor_unit=factor.unit, scope=emission.scope,
    )


@router.post("/run", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def run_scenario_endpoint(scenario_in: ScenarioCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    check_facility_access(current_user, scenario_in.facility_id)
    from models.period import Period
    from models.facility import Facility
    
    facility = db.get(Facility, scenario_in.facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
        
    period = db.get(Period, scenario_in.baseline_period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    stmt = select(ActivityRecord).where(
        ActivityRecord.facility_id == scenario_in.facility_id,
        ActivityRecord.period_start == period.start_date,
        ActivityRecord.period_end == period.end_date,
        # Baseline a what-if projection on reviewed activity only.
        ActivityRecord.confirmed_by_user.is_(True),
    ).limit(1)
    record = db.execute(stmt).scalar_one_or_none()
    
    baseline_activity = {}
    if record:
        baseline_activity = {
            "id": str(record.id),
            "activity_type": record.activity_type,
            "quantity": record.quantity,
            "unit": record.unit,
        }
    
    modified_dict = scenario_in.modified_inputs.model_dump(exclude_unset=True)
    
    try:
        result = run_scenario(db, baseline_activity, modified_dict, facility.region_code, period.end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    db_scenario = Scenario(
        facility_id=scenario_in.facility_id,
        baseline_period_id=scenario_in.baseline_period_id,
        modified_inputs=json.dumps(result["inputs_used"]),
        result_co2e_kg=result["result_co2e_kg"]
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario


@router.get("/", response_model=list[ScenarioResponse])
def list_scenarios(facility_id: uuid.UUID | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    if facility_id:
        check_facility_access(current_user, facility_id)
    elif current_user.role.name != "admin":
        facility_id = current_user.facility_id

    stmt = select(Scenario)
    if facility_id:
        stmt = stmt.where(Scenario.facility_id == facility_id)
    return db.execute(stmt).scalars().all()
