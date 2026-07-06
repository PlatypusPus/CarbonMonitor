"""Emission data queries — TODO: migrate from Elasticsearch to Postgres.

All functions here previously queried Elasticsearch (emissions-live / emissions-uploads indices).
Elasticsearch has been removed from the stack. These stubs return empty results until the
new pipeline is wired up:

  ActivityRecord → services.calculation → calculated_emissions (Postgres)

Each function below documents what it should eventually query.
"""

from typing import Any


def query_latest(
    metric: str | None = None,
    source: str | None = None,
    facility: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    # TODO: query calculated_emissions joined with activity_records
    # Filter by activity_type (metric), source, facility_id; order by calculated_at desc
    return []


def query_timeseries(
    metric: str,
    interval: str = "1h",
    source: str | None = None,
) -> list[dict[str, Any]]:
    # TODO: aggregate co2e_kg from calculated_emissions grouped by time bucket
    # activity_type replaces metric; use period_start from activity_records for bucketing
    return []


def query_crossverify(
    metric: str,
    interval: str = "1d",
    source: str | None = None,
) -> list[dict[str, Any]]:
    # TODO: compare calculated_emissions where source='csv' vs source='manual'/'ocr'
    # for the same facility + period, flagging discrepancies
    return []


def query_summary() -> list[dict[str, Any]]:
    # TODO: aggregate calculated_emissions by activity_type —
    # count, avg co2e_kg, latest calculated_at, latest emission_factor unit
    return []
