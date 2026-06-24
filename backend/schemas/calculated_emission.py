"""Request/response schemas for CalculatedEmission."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CalculatedEmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activity_record_id: uuid.UUID
    scope: int
    co2e_kg: float
    emission_factor_id: uuid.UUID
    calculated_at: datetime
