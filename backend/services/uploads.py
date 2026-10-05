"""Parse uploaded emission CSVs/XLSX files."""

import csv
import io
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.ocr_draft import OCRDraft
from schemas.activity_record import ACTIVITY_UNITS, ActivityValues
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
    if reader.fieldnames:
        reader.fieldnames = [header.strip() for header in reader.fieldnames]
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
        unit = (raw.get("unit") or "").strip() or ACTIVITY_UNITS[metric]
        try:
            ActivityValues(activity_type=metric, quantity=value, unit=unit)
        except ValueError as exc:
            raise ValueError(f"row {line_no}: {exc}") from exc
        try:
            timestamp = _parse_timestamp(raw.get("timestamp"))
        except ValueError as exc:
            raise ValueError(f"row {line_no}: {exc}") from exc
        rows.append(
            {
                "timestamp": timestamp,
                "metric": metric,
                "value": value,
                "unit": unit,
                "facility_name": (raw.get("facility_name") or "").strip() or None,
                "source": "upload",
            }
        )
    if not rows:
        raise ValueError("CSV contains no data rows")
    return rows


def convert_xlsx_to_csv_bytes(content: bytes) -> bytes:
    """Convert an electricity workbook to CSV rows.

    Uses the same header-based parser and quantity rule as the Excel intake path
    and the preview, so all three agree on which column is the activity quantity.
    """
    from services.excel.normalizer import normalize_workbook, select_activity_quantity
    from services.excel.parser import parse_workbook

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "metric", "value", "unit", "facility_name"])
    for record in normalize_workbook(parse_workbook(content, filename="upload.xlsx")):
        quantity, unit, _ = select_activity_quantity(record)
        if quantity is None:
            continue
        dt = datetime.combine(record.period_start, datetime.min.time(), tzinfo=timezone.utc)
        writer.writerow([dt.isoformat(), "electricity", quantity, unit, ""])
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

    Uses database unique constraint (uq_ocr_draft_key) for concurrency-safe
    idempotency. Inserts are attempted for each row; conflicts are caught and
    skipped, making this safe under concurrent uploads and duplicate rows in
    the same file.
    """
    staged: list[OCRDraft] = []
    for row in rows:
        period_start = datetime.fromisoformat(row["timestamp"])
        period_end = next_period_end(period_start)
        metric = row["metric"]
        quantity = row["value"]
        unit = row.get("unit") or ACTIVITY_UNITS[metric]

        # Pre-check avoids unnecessary INSERT attempts for the common case
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

        draft = build_draft(
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
        try:
            db.add(draft)
            db.commit()
            db.refresh(draft)
            staged.append(draft)
        except IntegrityError:
            db.rollback()
            # Unique constraint violated — another row in this upload or a
            # concurrent upload already inserted this draft key. Skip.
            continue
    return staged
