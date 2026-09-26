"""Parse uploaded emission CSVs/XLSX files."""

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from models.ocr_draft import OCRDraft
from services.drafts import SOURCE_TYPE_UPLOAD, build_draft, draft_exists

REQUIRED_COLUMNS = {"timestamp", "metric", "value"}
ALLOWED_METRICS = {"electricity", "diesel", "petrol", "lpg"}


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
        if metric not in ALLOWED_METRICS:
            raise ValueError(f"row {line_no}: unknown metric '{metric}' — expected one of {', '.join(sorted(ALLOWED_METRICS))}")
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


def convert_xlsx_to_csv_bytes(content: bytes) -> bytes:
    """Convert xlsx (MescomBill format) to CSV with timestamp/metric/value/unit/facility_name."""
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "metric", "value", "unit", "facility_name"])

    epoch = datetime(1899, 12, 30, tzinfo=timezone.utc)
    for row in ws.iter_rows(min_row=2, values_only=True):
        month_val = row[0]  # column A: datetime or serial number
        total_units = row[19]  # column T: Total Units (0-indexed)
        if month_val is None or total_units is None:
            continue
        # openpyxl may return datetime or int/float serial
        if hasattr(month_val, "isoformat"):
            dt = month_val.replace(tzinfo=timezone.utc) if month_val.tzinfo is None else month_val
        else:
            dt = epoch + timedelta(days=int(month_val))
        writer.writerow([dt.isoformat(), "electricity", total_units, "kWh", ""])

    return buf.getvalue().encode("utf-8")


def next_period_end(period_start: datetime) -> datetime:
    """First instant of the month after ``period_start`` (monthly billing period)."""
    if period_start.month == 12:
        return period_start.replace(year=period_start.year + 1, month=1, day=1)
    return period_start.replace(month=period_start.month + 1, day=1)


def stage_upload_drafts(
    db: Session,
    *,
    user_id: UUID,
    facility_id: UUID,
    filename: str,
    rows: list[dict[str, Any]],
) -> list[OCRDraft]:
    """Stage parsed upload rows as reviewable drafts.

    Nothing is written to ``activity_records``/``calculated_emissions`` here —
    that only happens once a reviewer confirms the draft, so an unreviewed
    upload can never reach a dashboard. Rows already staged or confirmed for
    this facility and source are skipped, which makes re-uploading a file a
    no-op instead of a double count.
    """
    staged: list[OCRDraft] = []
    for row in rows:
        period_start = datetime.fromisoformat(row["timestamp"])
        period_end = next_period_end(period_start)
        metric = row["metric"]
        quantity = row["value"]
        unit = row.get("unit") or "kWh"
        if draft_exists(
            db,
            facility_id=facility_id,
            period_start=period_start,
            period_end=period_end,
            activity_type=metric,
            quantity=quantity,
            unit=unit,
            source_type=SOURCE_TYPE_UPLOAD,
        ):
            continue
        staged.append(
            build_draft(
                user_id=user_id,
                facility_id=facility_id,
                source_filename=filename,
                source_type=SOURCE_TYPE_UPLOAD,
                period_start=period_start,
                period_end=period_end,
                activity_type=metric,
                quantity=quantity,
                unit=unit,
            )
        )
    if staged:
        db.add_all(staged)
        db.commit()
        for draft in staged:
            db.refresh(draft)
    return staged
