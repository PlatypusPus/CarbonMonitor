"""Request/response schemas for Recommendation."""

import uuid
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    period_id: uuid.UUID
    rule_id: str
    message: str
    supporting_numbers: dict[str, Any] | None = None
    created_at: datetime

    @field_validator("supporting_numbers", mode="before")
    @classmethod
    def parse_supporting_numbers(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v
