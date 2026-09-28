"""Request/response schemas for Facility."""

import uuid
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FacilityType = Literal["office", "warehouse", "data_center", "manufacturing"]


class FacilityCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    region_code: str | None = Field(default=None, max_length=50)
    facility_type: FacilityType | None = None

class FacilityUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    region_code: str | None = Field(default=None, max_length=50)
    facility_type: FacilityType | None = None


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location: str | None = Field(default=None, max_length=255)
    region_code: str | None = Field(default=None, max_length=50)
    facility_type: str | None = None
    created_at: datetime
