"""Flagged anomaly records and detection triggers."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db

from dependencies import get_current_user
from models.user import User
from schemas.anomaly import AnomalyRecord
from services import anomaly as anomaly_service

router = APIRouter()


@router.get("", response_model=list[AnomalyRecord])
def list_anomalies(
    metric: str | None = None,
    facility: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    return anomaly_service.query_anomalies(db, metric, facility, limit)


@router.post("/run", response_model=dict[str, int])
def run_anomaly_detection(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Manually trigger the anomaly detection job."""
    count = anomaly_service.run_detection(db)
    return {"anomalies_detected": count}
