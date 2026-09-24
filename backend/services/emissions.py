"""Emission data queries against Postgres."""

from typing import Any

from sqlalchemy.orm import Session

from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission


def query_latest(
    db: Session,
    metric: str | None = None,
    source: str | None = None,
    facility: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Latest calculated emissions, newest first."""
    from models.facility import Facility

    q = db.query(CalculatedEmission, ActivityRecord, Facility).join(
        ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id
    ).outerjoin(Facility, ActivityRecord.facility_id == Facility.id)
    if metric:
        q = q.filter(ActivityRecord.activity_type == metric)
    if source:
        q = q.filter(ActivityRecord.source == source)
    if facility:
        q = q.filter(Facility.name == facility)
    q = q.order_by(CalculatedEmission.calculated_at.desc()).limit(limit)
    return [
        {
            "timestamp": ar.period_start,
            "source": ar.source,
            "metric": ar.activity_type,
            "value": ce.co2e_kg,
            "unit": "kg CO2e",
            "facility_name": fac.name if fac else None,
        }
        for ce, ar, fac in q.all()
    ]


_INTERVAL_MAP = {
    "15m": ("15 minutes", "date_bin"),
    "1h": ("hour", "trunc"),
    "6h": ("6 hours", "date_bin"),
    "1d": ("day", "trunc"),
}


def query_timeseries(
    db: Session,
    metric: str,
    interval: str = "1h",
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Aggregate co2e_kg by time bucket (period_start)."""
    from sqlalchemy import func, text

    if interval not in _INTERVAL_MAP:
        interval = "1h"

    bucket_expr: Any
    if interval == "1h":
        bucket_expr = func.date_trunc("hour", ActivityRecord.period_start)
    elif interval == "1d":
        bucket_expr = func.date_trunc("day", ActivityRecord.period_start)
    elif interval in ("15m", "6h"):
        # date_bin requires origin; use 2001-01-01
        stride = "15 minutes" if interval == "15m" else "6 hours"
        bucket_expr = func.date_bin(text(f"'{stride}'"), ActivityRecord.period_start, text("'2001-01-01'::timestamptz"))
    else:
        bucket_expr = func.date_trunc("hour", ActivityRecord.period_start)

    q = (
        db.query(
            bucket_expr.label("bucket"),
            func.sum(CalculatedEmission.co2e_kg).label("value"),
            func.count(CalculatedEmission.id).label("count"),
        )
        .join(ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .filter(ActivityRecord.activity_type == metric)
        .group_by(text("bucket"))
        .order_by(text("bucket"))
    )
    if source:
        q = q.filter(ActivityRecord.source == source)
    return [
        {"timestamp": r.bucket, "value": float(r.value) if r.value is not None else None, "count": r.count}
        for r in q.all()
    ]


def query_crossverify(
    db: Session,
    metric: str,
    interval: str = "1d",
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Compare csv vs live (non-csv) per time bucket with discrepancy %."""
    # source param ignored for cross-verify — always compares csv vs non-csv
    upload_rows = {r["timestamp"]: r for r in query_timeseries(db, metric, interval, source="csv")}
    # filter live to exclude csv: reuse query but we need non-csv — do manual query
    # if live_rows currently includes all sources, recompute non-csv separately
    from sqlalchemy import func, text

    if interval not in _INTERVAL_MAP:
        interval = "1d"
    if interval == "1h":
        bucket_expr = func.date_trunc("hour", ActivityRecord.period_start)
    elif interval == "1d":
        bucket_expr = func.date_trunc("day", ActivityRecord.period_start)
    elif interval in ("15m", "6h"):
        stride = "15 minutes" if interval == "15m" else "6 hours"
        bucket_expr = func.date_bin(text(f"'{stride}'"), ActivityRecord.period_start, text("'2001-01-01'::timestamptz"))
    else:
        bucket_expr = func.date_trunc("hour", ActivityRecord.period_start)

    live_q = (
        db.query(
            bucket_expr.label("bucket"),
            func.sum(CalculatedEmission.co2e_kg).label("value"),
        )
        .join(ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .filter(ActivityRecord.activity_type == metric)
        .filter(ActivityRecord.source != "csv")
        .group_by(text("bucket"))
        .order_by(text("bucket"))
    )
    live_map = {r.bucket: float(r.value) for r in live_q.all()}
    upload_map = {r["timestamp"]: r["value"] for r in upload_rows.values()}

    all_buckets = sorted(set(live_map) | set(upload_map))
    out: list[dict[str, Any]] = []
    for b in all_buckets:
        lv = live_map.get(b)
        uv = upload_map.get(b)
        disc = None
        if lv is not None and lv != 0 and uv is not None:
            disc = ((uv - lv) / lv) * 100
        elif lv is None and uv is not None:
            disc = None
        out.append({"timestamp": b, "live_value": lv, "upload_value": uv, "discrepancy_pct": disc})
    return out


def query_summary(db: Session) -> list[dict[str, Any]]:
    """Aggregate co2e_kg by activity_type with chronological latest."""
    from sqlalchemy import func

    # aggregate count / avg per metric
    agg = (
        db.query(
            ActivityRecord.activity_type.label("metric"),
            func.count(CalculatedEmission.id).label("count"),
            func.avg(CalculatedEmission.co2e_kg).label("avg_value"),
        )
        .join(ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .group_by(ActivityRecord.activity_type)
        .all()
    )
    # true chronological latest per metric (distinct on)
    latest_rows = (
        db.query(
            ActivityRecord.activity_type.label("metric"),
            CalculatedEmission.co2e_kg.label("latest_value"),
            CalculatedEmission.calculated_at.label("latest_timestamp"),
        )
        .join(ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .distinct(ActivityRecord.activity_type)
        .order_by(ActivityRecord.activity_type, CalculatedEmission.calculated_at.desc())
        .all()
    )
    latest_map = {r.metric: r for r in latest_rows}
    return [
        {
            "metric": r.metric,
            "count": r.count,
            "avg_value": float(r.avg_value) if r.avg_value is not None else None,
            "latest_value": float(latest_map[r.metric].latest_value) if r.metric in latest_map else None,
            "unit": "kg CO2e",
            "latest_timestamp": latest_map[r.metric].latest_timestamp if r.metric in latest_map else None,
        }
        for r in agg
    ]
