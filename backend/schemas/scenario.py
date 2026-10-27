"""Request/response schemas for Scenario."""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ScenarioPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity_record_id: uuid.UUID
    quantity: float = Field(ge=0, allow_inf_nan=False)


class ScenarioComparison(BaseModel):
    activity_record_id: uuid.UUID
    baseline_quantity: float
    proposed_quantity: float
    unit: str
    baseline_co2e_kg: float
    projected_co2e_kg: float
    savings_co2e_kg: float
    savings_percent: float | None
    factor_value: float
    factor_unit: str
    scope: int

