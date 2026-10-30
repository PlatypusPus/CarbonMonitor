"""Scenarios router — what-if simulation endpoints."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, check_facility_access
from models.user import User
from models.activity_record import ActivityRecord
from schemas.scenario import ScenarioPreview, ScenarioComparison, ScenarioAsk, ScenarioAnswer
from services.scenario import run_scenario
from services.scenario_ai import plan_scenario
from routers.activity import list_activity_records

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



@router.post("/ask", response_model=ScenarioAnswer)
def ask_scenario(payload: ScenarioAsk, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)) -> ScenarioAnswer:
    """Turn a plain-language what-if into quantity changes, then calculate them here."""
    # ponytail: newest 300 records only; page or filter by facility if prompts need older history
    records = list_activity_records(db=db, user=current_user, facility_id=None, confirmed_only=True)[:300]
    if not records:
        raise HTTPException(status_code=400, detail="No confirmed records yet")
    labels = {f"r{i}": record for i, record in enumerate(records, 1)}
    plan = plan_scenario(payload.prompt, labels, db)
    changes, reasons, skipped = [], [], []
    for change in plan.changes:
        record = labels.get(change.record)
        if record is None or not change.proposed_quantity >= 0:
            skipped.append(f"{change.record}: invalid suggestion")
            continue
        try:
            changes.append(preview_scenario(ScenarioPreview(activity_record_id=record.id,
                quantity=change.proposed_quantity), db, current_user))
            reasons.append(change.reason)
        except HTTPException as error:
            skipped.append(f"{record.activity_type} {record.period_start:%b %Y}: {error.detail}")
    baseline = sum(c.baseline_co2e_kg for c in changes)
    projected = sum(c.projected_co2e_kg for c in changes)
    return ScenarioAnswer(explanation=plan.explanation, changes=changes, reasons=reasons, skipped=skipped,
        baseline_co2e_kg=baseline, projected_co2e_kg=projected, savings_co2e_kg=baseline - projected)
