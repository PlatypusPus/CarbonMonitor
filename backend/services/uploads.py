"""Parse uploaded emission CSVs and index them into Elasticsearch."""

# TODO (separate task): Refactor this module to accept raw activity data instead of pre-computed values.
#
# Current behaviour: caller provides a pre-computed "value" field (already a CO2e number or a
# sensor reading in unknown units), which is indexed as-is into Elasticsearch.
#
# Target behaviour: caller provides raw consumption quantities (e.g. kWh, litres of diesel)
# along with activity_type and unit. This module should write an ActivityRecord to Postgres
# and hand off to services.calculation.calculate_emissions() to derive co2e_kg.
#
# Do NOT change the current CSV parsing logic until the new ActivityRecord model and
# calculation service are implemented — the two paths should be switched atomically.

import csv
import io
from datetime import datetime
from typing import Any

from elasticsearch.helpers import bulk

from services.es import get_es_client

UPLOAD_INDEX = "emissions-uploads"
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
    actions = [
        {
            "_index": UPLOAD_INDEX,
            "_source": {**row, "upload_id": upload_id, "@timestamp": row["timestamp"]},
        }
        for row in rows
    ]
    success, _ = bulk(get_es_client(), actions)
    return success
