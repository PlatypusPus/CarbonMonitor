"""Emission readings and aggregations served from Postgres."""

from typing import Any
from uuid import UUID
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, facility_scope
from models.user import User
from schemas.emissions import CrossVerifyPoint, EmissionRecord, MetricSummary, TimeseriesPoint
from services import emissions as emissions_service

router = APIRouter()


def date_range(start_date: date | None = None, end_date: date | None = None):
    if (start_date and end_date and start_date > end_date) or end_date == date.max:
        raise HTTPException(422, "Choose a valid date range with the start on or before the end")
    return (
        datetime.combine(start_date, time.min, timezone.utc) if start_date else None,
        datetime.combine(end_date + timedelta(days=1), time.min, timezone.utc) if end_date else None,
    )


@router.get("/latest", response_model=list[EmissionRecord])
def latest(
    metric: str | None = None,
    source: str | None = None,
    facility: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
    dates: tuple = Depends(date_range),
) -> Any:
    return emissions_service.query_latest(db, metric, source, facility, limit, facility_id=scope, start=dates[0], end=dates[1])


@router.get("/timeseries", response_model=list[TimeseriesPoint])
def timeseries(
    metric: str,
    interval: str = "1h",
    source: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
    dates: tuple = Depends(date_range),
) -> Any:
    return emissions_service.query_timeseries(db, metric, interval, source, facility_id=scope, start=dates[0], end=dates[1])


@router.get("/summary", response_model=list[MetricSummary])
def summary(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
    dates: tuple = Depends(date_range),
) -> Any:
    return emissions_service.query_summary(db, facility_id=scope, start=dates[0], end=dates[1])


@router.get("/crossverify", response_model=list[CrossVerifyPoint])
def crossverify(
    metric: str,
    interval: str = "1d",
    source: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
) -> Any:
    return emissions_service.query_crossverify(db, metric, interval, source, facility_id=scope)
