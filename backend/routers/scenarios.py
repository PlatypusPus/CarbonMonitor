"""Scenarios router — what-if simulation endpoints."""

import uuid
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.scenario import Scenario
from models.activity_record import ActivityRecord
from schemas.scenario import ScenarioCreate, ScenarioResponse
from services.scenario import run_scenario

router = APIRouter()


@router.post("/run", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def run_scenario_endpoint(scenario_in: ScenarioCreate, db: Session = Depends(get_db)) -> Any:
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
        ActivityRecord.period_end == period.end_date
    ).limit(1)
    record = db.execute(stmt).scalar_one_or_none()
    
    baseline_activity = {}
    if record:
        baseline_activity = {
            "id": record.id,
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
def list_scenarios(facility_id: uuid.UUID | None = None, db: Session = Depends(get_db)) -> Any:
    stmt = select(Scenario)
    if facility_id:
        stmt = stmt.where(Scenario.facility_id == facility_id)
    return db.execute(stmt).scalars().all()
