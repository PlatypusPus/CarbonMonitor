"""Scenarios router — what-if simulation endpoints."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, check_facility_access
from models.user import User
from models.activity_record import ActivityRecord
from schemas.scenario import ScenarioPreview, ScenarioComparison
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

