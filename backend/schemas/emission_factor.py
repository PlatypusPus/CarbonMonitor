"""Request/response schemas for EmissionFactor."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ActivityType = Literal["electricity", "diesel", "petrol", "lpg"]


class EmissionFactorCreate(BaseModel):
    activity_type: ActivityType
    region: str | None = None
    factor_value: float
    unit: str
    valid_from: datetime
    valid_to: datetime | None = None
    # TODO: factor_value must come from an authoritative source — do not accept arbitrary user input without review


class EmissionFactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activity_type: str
    region: str | None = None
    factor_value: float
    unit: str
    valid_from: datetime
    valid_to: datetime | None = None
    created_at: datetime
