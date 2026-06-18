"""Flagged anomaly records and detection triggers."""

from typing import Any

from elasticsearch import ConnectionError as ESConnectionError
from fastapi import APIRouter, Depends, HTTPException, Query, status

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
) -> Any:
    try:
        return anomaly_service.query_anomalies(metric, facility, limit)
    except ESConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch unavailable",
        ) from exc
