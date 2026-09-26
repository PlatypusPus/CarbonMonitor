"""Normalize parsed electricity rows into :class:`NormalizedElectricityRecord`.

Each input row becomes exactly one normalized record. Dates are parsed into a
monthly period (period_start at the start of the month, period_end at the last
day of that month via ``calendar.monthrange`` — no hardcoded month lengths).
Null/empty cells are left as ``None``; a present-but-unparseable numeric cell is
a row-level error. Original filename, row number, source columns, and raw
values are preserved for provenance.

The final carbon-accounting quantity is intentionally NOT chosen here — it is
isolated in :func:`select_activity_quantity`, the single business-rule boundary.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime

from schemas.normalized_electricity import NormalizedElectricityRecord
from services.excel.mappings import ELECTRICITY_COLUMN_MAPPINGS
from services.excel.parser import ParsedExcelRow, ParsedWorkbook

_MONTH_FORMATS = (
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%Y-%m",
    "%b %Y",
    "%B %Y",
    "%b-%y",
    "%d-%b-%Y",
)
_NUMERIC = re.compile(r"[^\d.+-]")


def _parse_number(value: object) -> float | None:
    """Parse a numeric cell, tolerating currency symbols, spaces, and commas.

    Indian thousand grouping (``1,34,050``) is handled by stripping every comma.
    Empty/None cells -> None; present-but-unparseable values raise a row error.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"boolean value '{value}' is not a valid number")
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).strip()
    if not cleaned:
        return None
    compact = _NUMERIC.sub("", cleaned)
    if not compact or compact in {"+", "-", "."}:
        raise ValueError(f"invalid numeric value '{value}'")

    parts = compact.split(".")
    if len(parts) > 2:
        compact = f"{parts[0]}.{''.join(parts[1:])}"
    try:
        return float(compact)
    except ValueError as exc:
        raise ValueError(f"invalid numeric value '{value}'") from exc


def _parse_month_start(value: object) -> date:
    """Return the first day of the month for a monthly period cell."""
    if isinstance(value, datetime):
        return value.date().replace(day=1)
    if isinstance(value, date):
        return value.replace(day=1)
    if value is None:
        raise ValueError("missing Month value")
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError("missing Month value")

    try:
        return date.fromisoformat(cleaned[:10]).replace(day=1)
    except ValueError:
        pass

    for fmt in _MONTH_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date().replace(day=1)
        except ValueError:
            continue
    raise ValueError(f"invalid Month '{value}'")


def _month_end(month_start: date) -> date:
    _, last_day = calendar.monthrange(month_start.year, month_start.month)
    return month_start.replace(day=last_day)


def _display_value(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""
    return str(value)


def normalize_row(row: ParsedExcelRow, *, filename: str) -> NormalizedElectricityRecord:
    """Normalize a single parsed row into one :class:`NormalizedElectricityRecord`."""
    data = row.as_dict()

    month_header = next(
        (header for header, concept in ELECTRICITY_COLUMN_MAPPINGS.items() if concept.field == "period"),
        None,
    )
    if month_header is None or month_header not in data:
        raise ValueError("missing Month column")
    if not _present(data[month_header]):
        raise ValueError("missing Month value")

    period_start = _parse_month_start(data[month_header])
    period_end = _month_end(period_start)

    normalized: dict[str, float] = {}
    source_columns: dict[str, str] = {}
    for header, concept in ELECTRICITY_COLUMN_MAPPINGS.items():
        if concept.field == "period" or header not in data:
            continue
        if not _present(data[header]):
            continue  # null/empty cells map to None, never to 0
        number = _parse_number(data[header])
        if number is None:
            continue
        normalized[concept.field] = number
        source_columns[header] = concept.field

    raw_values = {
        raw_header: _display_value(value)
        for raw_header, value in zip(row.raw_headers, row.values)
    }

    return NormalizedElectricityRecord(
        period_start=period_start,
        period_end=period_end,
        **normalized,
        source_filename=filename,
        source_row=row.row_number,
        source_columns=source_columns,
        raw_values=raw_values,
    )


def normalize_workbook(parsed: ParsedWorkbook) -> list[NormalizedElectricityRecord]:
    """Normalize every data row, failing loudly with per-row error messages."""
    records: list[NormalizedElectricityRecord] = []
    errors: list[str] = []
    for row in parsed.rows:
        try:
            records.append(normalize_row(row, filename=parsed.filename))
        except ValueError as exc:
            errors.append(f"row {row.row_number}: {exc}")
    if errors:
        raise ValueError("; ".join(errors))
    return records


def select_activity_quantity(
    record: NormalizedElectricityRecord,
) -> tuple[float | None, str, str | None]:
    """
    TEMPORARY BUSINESS RULE.

    Selects the quantity used to create ActivityRecordCreate.

    IMPORTANT:
    This is NOT the final CarbonTrace electricity accounting rule.
    Currently uses MESCOM supplied units only so that Excel ingestion
    can be tested end-to-end.

    Before production carbon calculations are enabled, this function
    MUST be replaced with the approved electricity accounting rule,
    including the final kWh/kVAh decision.
    """
    if record.grid_import_kwh is not None:
        return record.grid_import_kwh, "kWh", "mescom units"

    return None, "kWh", None


def _present(value: object) -> bool:
    return value is not None and not (isinstance(value, str) and not value.strip())