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
