"""Parse uploaded emission CSVs.

TODO: Once the ActivityRecord pipeline is ready, replace index_upload_readings() with:
  - validate each row against ActivityRecordCreate schema
  - write one ActivityRecord per row (source="csv", confirmed_by_user=False)
  - trigger services.calculation.calculate_emissions() for each
  - do NOT index to Elasticsearch (removed from stack)

The CSV column names (timestamp/metric/value) will also need to change to match
ActivityRecord fields (period_start, activity_type, quantity, unit).
Switch the two halves atomically — don't half-migrate.
"""

import csv
import io
from datetime import datetime
from typing import Any

REQUIRED_COLUMNS = {"timestamp", "metric", "value"}


def _parse_timestamp(value: str | None) -> str:
    if not value or not value.strip():
        raise ValueError("missing timestamp")
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid timestamp '{value}'") from exc


def parse_emissions_csv(content: bytes) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    headers = {header.strip() for header in (reader.fieldnames or [])}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(reader, start=2):
        try:
            value = float(raw["value"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"row {line_no}: 'value' must be numeric") from exc
        metric = (raw.get("metric") or "").strip()
        if not metric:
            raise ValueError(f"row {line_no}: 'metric' is required")
        try:
            timestamp = _parse_timestamp(raw.get("timestamp"))
        except ValueError as exc:
            raise ValueError(f"row {line_no}: {exc}") from exc
        rows.append(
            {
                "timestamp": timestamp,
                "metric": metric,
                "value": value,
                "unit": (raw.get("unit") or "").strip() or None,
                "facility_name": (raw.get("facility_name") or "").strip() or None,
                "source": "upload",
            }
        )
    if not rows:
        raise ValueError("CSV contains no data rows")
    return rows


def index_upload_readings(upload_id: str, rows: list[dict[str, Any]]) -> int:
    # TODO: replace with ActivityRecord creation + calculation pipeline (see module docstring)
    # Returning 0 until the new pipeline is in place — the Upload record is still written to Postgres.
    return 0
