"""Emission readings and aggregations served from Postgres."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, facility_scope
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
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
) -> Any:
    return emissions_service.query_latest(db, metric, source, facility, limit, facility_id=scope)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
def timeseries(
    metric: str,
    interval: str = "1h",
    source: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
) -> Any:
    return emissions_service.query_timeseries(db, metric, interval, source, facility_id=scope)


@router.get("/summary", response_model=list[MetricSummary])
def summary(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    scope: UUID | None = Depends(facility_scope),
) -> Any:
    return emissions_service.query_summary(db, facility_id=scope)


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
