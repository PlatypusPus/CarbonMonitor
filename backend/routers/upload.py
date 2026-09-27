"""CSV/XLSX data uploads for cross-verification against API-sourced emissions."""

import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import check_facility_access, require_role
from models.facility import Facility
from models.upload import Upload
from models.user import User
from schemas.upload import UploadPreviewResponse, UploadResponse
from services.uploads import (
    convert_xlsx_to_csv_bytes,
    parse_emissions_csv,
    stage_upload_drafts,
)

logger = logging.getLogger(__name__)

router = APIRouter()

PREVIEW_COLUMNS = ["timestamp", "metric", "value", "unit", "facility_name"]
PREVIEW_ROW_LIMIT = 5
# Curated set of columns worth previewing from an electricity workbook.
# Anything not present in the sheet is simply skipped.
PREVIEW_IMPORTANT_HEADERS = {
    "month",
    "total units",
    "net units",
    "net bill",
    "per unit",
    "unit used",
}


def _display_cell(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        rounded = round(value, 2)
        return str(int(rounded)) if rounded.is_integer() else str(rounded)
    text = str(value).strip()
    return text or None


@router.post("/preview", response_model=UploadPreviewResponse)
async def preview_upload(
    file: UploadFile = File(...),
    facility_id: UUID | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> UploadPreviewResponse:
    """Parse a CSV/XLSX and return its columns plus the first few rows.

    XLSX files show the real workbook's important columns (month/units/billing)
    plus the facility the rows will be assigned to. Runs the same validation as
    the real ingest, so it doubles as a dry run: invalid files get a 422 with
    the parse error instead of being ingested.
    """
    content = await file.read()
    is_xlsx = (file.filename or "").lower().endswith(".xlsx")

    try:
        if is_xlsx:
            # Use the same Excel parser as the real ingestion path
            from services.excel.parser import parse_workbook
            from services.excel.detector import detect_electricity_workbook

            parsed = parse_workbook(content, filename=file.filename or "excel-upload")

            if not detect_electricity_workbook(parsed):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{parsed.filename}: not recognized as an electricity workbook",
                )

            target_facility_id = facility_id or user.facility_id
            if target_facility_id is not None:
                check_facility_access(user, target_facility_id)
            facility = db.get(Facility, target_facility_id) if target_facility_id else None

            # Use normalized headers and first few data rows for preview
            columns = list(parsed.headers)
            # Filter out empty headers
            columns = [c for c in columns if c]

            # Map normalized -> raw for display
            header_map = dict(zip(parsed.headers, parsed.raw_headers))

            # Get first few data rows
            preview_rows = []
            for row in parsed.rows[:PREVIEW_ROW_LIMIT]:
                row_data = []
                for header in parsed.headers:
                    if header:
                        value = row.values[parsed.headers.index(header)]
                        row_data.append(_display_cell(value))
                if facility and facility.name:
                    row_data.append(facility.name)
                preview_rows.append(row_data)

            columns_display = [header_map.get(c, c) for c in columns]
            if facility and facility.name:
                columns_display.append("Facility")

            return UploadPreviewResponse(
                filename=file.filename or "excel-upload",
                columns=columns_display,
                rows=preview_rows,
                row_count=len(parsed.rows),
            )
        else:
            # CSV path unchanged
            csv_bytes = content
            rows = parse_emissions_csv(csv_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse xlsx: {exc}",
        ) from exc

    return UploadPreviewResponse(
        filename=file.filename or "upload.csv",
        columns=PREVIEW_COLUMNS,
        rows=[
            [_display_cell(row.get(column)) for column in PREVIEW_COLUMNS]
            for row in rows[:PREVIEW_ROW_LIMIT]
        ],
        row_count=len(rows),
    )


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    facility_id: UUID | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> Upload:
    """Stage a CSV/XLSX for review.

    Rows become ``OCRDraft`` records (source_type="upload") that a reviewer
    confirms on the intake page — the same lifecycle OCR and Excel intake use.
    Nothing reaches ``activity_records``/``calculated_emissions`` until then, so
    an unreviewed upload can't move a dashboard. Rows already staged or
    confirmed are skipped, so re-uploading a file is a no-op rather than a
    double count.

    ``facility_id`` is the facility picked in the intake UI; it defaults to the
    facility attached to the account.
    """
    if facility_id is not None:
        check_facility_access(user, facility_id)
    target_facility = facility_id or user.facility_id
    if target_facility is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="no facility assigned to your account — ask an admin to set one",
        )

    content = await file.read()

    # detect xlsx and convert to CSV for pipeline
    if (file.filename or "").lower().endswith(".xlsx"):
        try:
            content = convert_xlsx_to_csv_bytes(content)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse xlsx: {exc}",
            ) from exc

    try:
        rows = parse_emissions_csv(content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    try:
        drafts = stage_upload_drafts(
            db,
            user_id=user.id,
            facility_id=target_facility,
            filename=file.filename or "upload.csv",
            rows=rows,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    record = Upload(
        user_id=user.id,
        facility_id=target_facility,
        filename=file.filename or "upload.csv",
        status="pending_review",
        row_count=len(drafts),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
