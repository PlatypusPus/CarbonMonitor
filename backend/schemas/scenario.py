"""Request/response schemas for Scenario."""

import uuid
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class ScenarioCreate(BaseModel):
    facility_id: uuid.UUID
    baseline_period_id: uuid.UUID
    modified_inputs: dict[str, Any]
    # TODO: define the shape of modified_inputs — which ActivityRecord fields can be overridden


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
