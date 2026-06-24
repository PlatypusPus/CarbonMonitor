"""Request/response schemas for ActivityRecord."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

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
    # TODO: OCR-sourced records should default confirmed_by_user=False and require a separate confirm endpoint


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
