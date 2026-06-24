"""Emission readings and aggregations served from Elasticsearch."""

from typing import Any

from fastapi import APIRouter, Depends, Query

from dependencies import get_current_user
from models.user import User
from schemas.emissions import CrossVerifyPoint, EmissionRecord, MetricSummary, TimeseriesPoint
from services import emissions as emissions_service

router = APIRouter()


@router.get("/latest", response_model=list[EmissionRecord])
def latest(
    metric: str | None = None,
    source: str | None = None,
    facility: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    _user: User = Depends(get_current_user),
) -> Any:
    return emissions_service.query_latest(metric, source, facility, limit)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
def timeseries(
    metric: str,
    interval: str = "1h",
    source: str | None = None,
    _user: User = Depends(get_current_user),
) -> Any:
    return emissions_service.query_timeseries(metric, interval, source)


@router.get("/summary", response_model=list[MetricSummary])
def summary(_user: User = Depends(get_current_user)) -> Any:
    return emissions_service.query_summary()


@router.get("/crossverify", response_model=list[CrossVerifyPoint])
def crossverify(
    metric: str,
    interval: str = "1d",
    source: str | None = None,
    _user: User = Depends(get_current_user),
) -> Any:
    return emissions_service.query_crossverify(metric, interval, source)
