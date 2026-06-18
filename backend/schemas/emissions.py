"""Response schemas for emission queries."""

from datetime import datetime

from pydantic import BaseModel


class EmissionRecord(BaseModel):
    timestamp: datetime | None = None
    source: str | None = None
    metric: str | None = None
    value: float | None = None
    unit: str | None = None
    facility_name: str | None = None
    region: str | None = None


class TimeseriesPoint(BaseModel):
    timestamp: datetime
    value: float | None = None
    count: int


class MetricSummary(BaseModel):
    metric: str
    count: int
    avg_value: float | None = None
    latest_value: float | None = None
    unit: str | None = None
    latest_timestamp: datetime | None = None
