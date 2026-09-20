"""Request/response schemas for Facility."""

import uuid
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict

FacilityType = Literal["office", "warehouse", "data_center", "manufacturing"]


class FacilityCreate(BaseModel):
    name: str
    location: str | None = None
    region_code: str | None = None
    facility_type: FacilityType | None = None


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location: str | None = None
    region_code: str | None = None
    facility_type: str | None = None
    created_at: datetime
