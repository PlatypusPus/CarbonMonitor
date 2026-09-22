"""Request/response schemas for ActivityRecord."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

ActivityType = Literal["electricity", "diesel", "petrol", "lpg"]
ActivitySource = Literal["manual", "csv", "ocr"]


class ActivityRecordCreate(BaseModel):
    facility_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    activity_type: ActivityType
    quantity: float
    unit: str
    source: ActivitySource
    confirmed_by_user: bool = False

    @model_validator(mode="after")
    def check_ocr_confirmed(self) -> "ActivityRecordCreate":
        if self.source == "ocr" and self.confirmed_by_user:
            self.confirmed_by_user = False
        return self

    @model_validator(mode="after")
    def validate_units(self) -> "ActivityRecordCreate":
        valid_units = {
            "electricity": "kWh",
            "diesel": "litre",
            "petrol": "litre",
            "lpg": "kg"
        }
        expected = valid_units.get(self.activity_type)
        if expected and self.unit != expected:
            raise ValueError(f"Invalid unit for {self.activity_type}. Expected {expected}, got {self.unit}")
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
