"""Request/response schemas for Scenario."""

import uuid
from typing import Literal

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



class ChatTurn(BaseModel):
    role: Literal["user", "model"]
    text: str = Field(min_length=1, max_length=4000)


class ScenarioAsk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatTurn] = Field(min_length=1, max_length=20)

    @field_validator("messages")
    @classmethod
    def ends_with_question(cls, value):
        if value[-1].role != "user" or len(value[-1].text) > 1000:
            raise ValueError("The last message must be a question of at most 1000 characters")
        return value


class ProposedChange(BaseModel):
    """A change to one past record. The AI never calculates emissions itself."""
    record: str
    proposed_quantity: float
    reason: str


class FutureChange(BaseModel):
    """An ongoing change applied to the forecast, e.g. -20% electricity from 2026-11."""
    activity_type: str
    change_percent: float
    start_month: str


class ScenarioPlan(BaseModel):
    reply: str
    changes: list[ProposedChange]
    future_changes: list[FutureChange]


class ForecastMonth(BaseModel):
    month: str
    baseline_co2e_kg: float
    projected_co2e_kg: float


class ScenarioAnswer(BaseModel):
    reply: str
    changes: list[ScenarioComparison]
    reasons: list[str]
    skipped: list[str]
    baseline_co2e_kg: float
    projected_co2e_kg: float
    savings_co2e_kg: float
    footprint_co2e_kg: float
    future_changes: list[FutureChange]
    forecast: list[ForecastMonth]
