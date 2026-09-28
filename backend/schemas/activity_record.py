"""Request/response schemas for ActivityRecord."""

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ActivityType = Literal["electricity", "diesel", "petrol", "lpg"]
ActivitySource = Literal["manual", "csv", "ocr", "excel"]
ACTIVITY_UNITS = {"electricity": "kWh", "diesel": "litre", "petrol": "litre", "lpg": "kg"}


class ActivityValues(BaseModel):
    activity_type: ActivityType
    quantity: float = Field(ge=0, allow_inf_nan=False)
    unit: str

    @model_validator(mode="after")
    def validate_units(self) -> "ActivityValues":
        expected = ACTIVITY_UNITS[self.activity_type]
        if self.unit != expected:
            raise ValueError(f"Invalid unit for {self.activity_type}. Expected {expected}, got {self.unit}")
        return self


class ActivityRecordCreate(ActivityValues):
    facility_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    source: ActivitySource
    confirmed_by_user: bool = False

    @model_validator(mode="after")
    def check_ocr_confirmed(self) -> "ActivityRecordCreate":
        if self.source == "ocr" and self.confirmed_by_user:
            self.confirmed_by_user = False
        return self

    @model_validator(mode="after")
    def validate_period(self) -> "ActivityRecordCreate":
        start = self.period_start
        end = self.period_end
        if (start.tzinfo is None) != (end.tzinfo is None):
            raise ValueError("Period dates must use consistent timezone information")
        if end.replace(tzinfo=end.tzinfo or timezone.utc) <= start.replace(tzinfo=start.tzinfo or timezone.utc):
            raise ValueError("period_end must be after period_start")
        return self


class ActivityRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    activity_type: str
    quantity: float
    unit: str
    source: str
    confirmed_by_user: bool
    created_at: datetime
