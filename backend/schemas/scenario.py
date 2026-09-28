"""Request/response schemas for Scenario."""

import uuid
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ScenarioInputsOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: float | None = None
    activity_type: str | None = None
    unit: str | None = None


class ScenarioCreate(BaseModel):
    facility_id: uuid.UUID
    baseline_period_id: uuid.UUID
    modified_inputs: ScenarioInputsOverride


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    baseline_period_id: uuid.UUID
    modified_inputs: dict[str, Any] | None = None
    result_co2e_kg: float | None = None
    created_at: datetime

    @field_validator("modified_inputs", mode="before")
    @classmethod
    def parse_modified_inputs(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v
