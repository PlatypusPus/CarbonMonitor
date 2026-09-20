"""Scenario simulator — what-if emission calculations that never touch real data tables."""


from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.emission_factor import EmissionFactor
from services.calculation import SCOPE_MAP


def run_scenario(db: Session, baseline_activity: dict[str, Any], modified_inputs: dict[str, Any]) -> dict[str, Any]:
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
        
    stmt = select(EmissionFactor).where(EmissionFactor.activity_type == act_type).limit(1)
    factor = db.execute(stmt).scalar_one_or_none()
    if not factor:
        raise ValueError(f"No emission factor found for activity type: {act_type}")
        
    scope = SCOPE_MAP.get(act_type, 1)
    quantity = float(hypothetical.get("quantity", 0))
    co2e_kg = quantity * factor.factor_value
    
    return {
        "result_co2e_kg": co2e_kg,
        "scope": scope,
        "inputs_used": hypothetical
    }
