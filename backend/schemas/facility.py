"""Request/response schemas for Facility."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FacilityCreate(BaseModel):
    name: str
    location: str | None = None
    region_code: str | None = None
    facility_type: str | None = None
    # TODO: validate facility_type against allowed enum values once defined


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location: str | None = None
    region_code: str | None = None
    facility_type: str | None = None
    created_at: datetime
