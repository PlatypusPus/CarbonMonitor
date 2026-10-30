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



class ScenarioAsk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=3, max_length=1000)


class ProposedChange(BaseModel):
    """One change the AI proposes. It never calculates emissions itself."""
    record: str
    proposed_quantity: float
    reason: str


class ScenarioPlan(BaseModel):
    explanation: str
    changes: list[ProposedChange]


class ScenarioAnswer(BaseModel):
    explanation: str
    changes: list[ScenarioComparison]
    reasons: list[str]
    skipped: list[str]
    baseline_co2e_kg: float
    projected_co2e_kg: float
    savings_co2e_kg: float
