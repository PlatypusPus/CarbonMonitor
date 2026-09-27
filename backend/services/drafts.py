"""Shared helpers for the intake-draft lifecycle.

Every ingestion path (OCR, Excel, CSV/XLSX upload) stages rows as ``OCRDraft``
records that a human confirms before they reach the emissions ledger. The
helpers here keep that staging idempotent: re-uploading a file must never
produce a second copy of a row that is already staged or already confirmed.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from models.ocr_draft import OCRDraft

# source_type values staged by the intake flows. "ocr" is the historical
# default and is kept in sync with OCRDraft.source_type's column default.
SOURCE_TYPE_OCR = "ocr"
SOURCE_TYPE_EXCEL = "excel"
SOURCE_TYPE_UPLOAD = "upload"

# How a draft's source_type maps onto ActivityRecord.source. The ledger's
# ``activity_source_enum`` predates the upload intake flow and has no "upload"
# member; uploaded CSV/XLSX rows have always been recorded as "csv", which is
# also what the cross-verification query treats as the "uploaded" side. Keeping
# the mapping here avoids widening the enum while leaving the two vocabularies
# explicitly related.
_DRAFT_SOURCE_TO_ACTIVITY_SOURCE = {
    SOURCE_TYPE_UPLOAD: "csv",
    SOURCE_TYPE_OCR: "ocr",
    SOURCE_TYPE_EXCEL: "excel",
}


def activity_source_for_draft(source_type: str) -> str:
    """Map a draft's ``source_type`` onto a valid ``ActivityRecord.source``."""
    from models.activity_record import SOURCES

    mapped = _DRAFT_SOURCE_TO_ACTIVITY_SOURCE.get(source_type, source_type)
    if mapped in SOURCES:
        return mapped
    return "csv"


def draft_exists(
    db: Session,
    *,
    facility_id: uuid.UUID,
    period_start: datetime,
    period_end: datetime,
    activity_type: str,
    quantity: float,
    unit: str,
    source_type: str,
) -> bool:
    """True when a draft for this exact row already exists.

    Matches on the values a re-upload would reproduce (facility, period,
    activity, quantity, unit and ingestion source). Already-confirmed drafts
    count too, so a file can't be re-ingested after it was confirmed.
    """
    return (
        db.query(OCRDraft.id)
        .filter(
            OCRDraft.facility_id == facility_id,
            OCRDraft.period_start == period_start,
            OCRDraft.period_end == period_end,
            OCRDraft.activity_type == activity_type,
            OCRDraft.quantity == quantity,
            OCRDraft.unit == unit,
            OCRDraft.source_type == source_type,
        )
        .first()
        is not None
    )


def build_draft(
    *,
    user_id: uuid.UUID,
    facility_id: uuid.UUID,
    source_filename: str,
    source_type: str,
    period_start: datetime,
    period_end: datetime,
    activity_type: str,
    quantity: float,
    unit: str,
    source_row: int | None = None,
    source_column: str | None = None,
    activity_record_id: uuid.UUID | None = None,
) -> OCRDraft:
    """Construct an unconfirmed draft. Persisting it is the caller's job."""
    return OCRDraft(
        user_id=user_id,
        source_filename=source_filename,
        source_type=source_type,
        source_row=source_row,
        source_column=source_column,
        facility_id=facility_id,
        period_start=period_start,
        period_end=period_end,
        activity_type=activity_type,
        quantity=quantity,
        unit=unit,
        status="draft",
        activity_record_id=activity_record_id,
    )
