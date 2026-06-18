"""Response schema for flagged anomalies."""

from datetime import datetime

from pydantic import BaseModel


class AnomalyRecord(BaseModel):
    timestamp: datetime | None = None
    metric: str | None = None
    facility_name: str | None = None
    value: float | None = None
    unit: str | None = None
    expected_value: float | None = None
    anomaly_score: float | None = None
    source: str | None = None
    region: str | None = None
