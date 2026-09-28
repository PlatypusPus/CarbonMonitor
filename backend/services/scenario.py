"""Scenario simulator — what-if emission calculations that never touch real data tables."""


from typing import Any
from sqlalchemy.orm import Session
from datetime import datetime
from schemas.activity_record import ActivityValues
from services.calculation import SCOPE_MAP
from services.factors import resolve_factor


def run_scenario(
    db: Session, 
    baseline_activity: dict[str, Any], 
    modified_inputs: dict[str, Any], 
    region_code: str | None, 
    period_end: datetime
) -> dict[str, Any]:
    allowed_keys = {"quantity", "activity_type", "unit"}
    for k in modified_inputs:
        if k not in allowed_keys:
            raise ValueError(f"Field '{k}' cannot be overridden in a scenario.")
            
    hypothetical = baseline_activity.copy()
    for k, v in modified_inputs.items():
        if v is not None:
            hypothetical[k] = v
    
    act_type = hypothetical.get("activity_type")
    if not act_type:
        raise ValueError("activity_type is missing")
        
    activity = ActivityValues.model_validate(hypothetical)
    factor = resolve_factor(db, act_type, period_end, region_code)
    if not factor:
        raise ValueError(f"No emission factor found for activity type: {act_type}")
        
    scope = SCOPE_MAP.get(act_type, 1)
    quantity = activity.quantity
    co2e_kg = quantity * factor.factor_value
    
    return {
        "result_co2e_kg": co2e_kg,
        "scope": scope,
        "inputs_used": hypothetical
    }
