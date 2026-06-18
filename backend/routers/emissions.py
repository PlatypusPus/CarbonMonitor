"""Emission readings and aggregations served from Elasticsearch."""

from collections.abc import Callable
from typing import Any

from elasticsearch import ConnectionError as ESConnectionError
from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import get_current_user
from models.user import User
from schemas.emissions import EmissionRecord, MetricSummary, TimeseriesPoint
from services import emissions as emissions_service

router = APIRouter()


def _run(func: Callable[..., Any], *args: Any) -> Any:
    try:
        return func(*args)
    except ESConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch unavailable",
        ) from exc


@router.get("/latest", response_model=list[EmissionRecord])
def latest(
    metric: str | None = None,
    source: str | None = None,
    facility: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    _user: User = Depends(get_current_user),
) -> Any:
    return _run(emissions_service.query_latest, metric, source, facility, limit)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
def timeseries(
    metric: str,
    interval: str = "1h",
    source: str | None = None,
    _user: User = Depends(get_current_user),
) -> Any:
    return _run(emissions_service.query_timeseries, metric, interval, source)


@router.get("/summary", response_model=list[MetricSummary])
def summary(_user: User = Depends(get_current_user)) -> Any:
    return _run(emissions_service.query_summary)
