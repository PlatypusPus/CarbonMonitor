"""Normalized emission reading shared by every data source before ingestion."""

from datetime import datetime

from pydantic import BaseModel


class EmissionReading(BaseModel):
    timestamp: datetime
    source: str
    metric: str
    value: float
    unit: str
    facility_id: str | None = None
    facility_name: str | None = None
    region: str | None = None
