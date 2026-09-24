"""Activity records router — ingest and manage ActivityRecord entries."""

from datetime import UTC, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_role
from models.activity_record import ActivityRecord
from models.ocr_draft import OCRDraft
from models.user import User
from schemas.activity_record import ActivityRecordCreate, ActivityRecordResponse
from schemas.ocr_draft import OCRDraftResponse
from services.excel.detector import detect_electricity_workbook
from services.excel.normalizer import normalize_workbook, select_activity_quantity
from services.excel.parser import parse_workbook
from services.ocr import extract_activities_from_document

router = APIRouter()


@router.get("", response_model=list[OCRDraftResponse])
def list_activity_drafts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OCRDraft]:
    """List saved intake drafts, newest first.

    Admins see every draft; other users only see their own. Confirmed drafts
    stay visible with their linked activity_record_id, so the intake page can
    restore state after navigation.
    """
    query = db.query(OCRDraft)
    if user.role.name != "admin":
        query = query.filter(OCRDraft.user_id == user.id)
    return query.order_by(OCRDraft.created_at.desc()).all()


@router.post("/ocr", response_model=list[OCRDraftResponse], status_code=status.HTTP_201_CREATED)
async def create_ocr_draft(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> list[OCRDraft]:
    content = await file.read()
    try:
        extracted = extract_activities_from_document(content, file.filename)
        payloads = [
            ActivityRecordCreate.model_validate(
                {**record, "source": "ocr", "confirmed_by_user": False}
            )
            for record in extracted
        ]
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Idempotent re-uploads: never create a draft for a row already ingested.
    payloads = _filter_new_drafts(db, payloads, source_type="ocr")

    drafts = [
        OCRDraft(
            user_id=user.id,
            source_filename=file.filename or "ocr-upload",
            facility_id=payload.facility_id,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        for payload in payloads
    ]
    db.add_all(drafts)
    db.commit()
    for draft in drafts:
        db.refresh(draft)
    return drafts


def _validation_error_message(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )


def _draft_exists(db: Session, payload: ActivityRecordCreate, source_type: str) -> bool:
    """True when a draft for this exact row already exists.

    Matches on the values a re-upload would reproduce (facility, period,
    activity, quantity, unit and ingestion source). Already-confirmed drafts
    count too, so a file can't be re-ingested after it was confirmed.
    """
    return (
        db.query(OCRDraft.id)
        .filter(
            OCRDraft.facility_id == payload.facility_id,
            OCRDraft.period_start == payload.period_start,
            OCRDraft.period_end == payload.period_end,
            OCRDraft.activity_type == payload.activity_type,
            OCRDraft.quantity == payload.quantity,
            OCRDraft.unit == payload.unit,
            OCRDraft.source_type == source_type,
        )
        .first()
        is not None
    )


def _filter_new_drafts(
    db: Session, payloads: list[ActivityRecordCreate], source_type: str
) -> list[ActivityRecordCreate]:
    """Drop payloads that already exist as drafts (idempotent re-uploads)."""
    return [
        payload
        for payload in payloads
        if not _draft_exists(db, payload, source_type)
    ]


@router.post("/excel", response_model=list[OCRDraftResponse], status_code=status.HTTP_201_CREATED)
async def create_excel_drafts(
    file: UploadFile = File(...),
    facility_id: UUID | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> list[OCRDraft]:
    """Ingest an electricity workbook as reviewable drafts (source="excel").

    The Excel file has no facility_id, so it is supplied here (or defaults to
    the user's facility). Every normalized row becomes a draft that follows the
    exact same confirmation lifecycle as OCR drafts; nothing is auto-confirmed.
    """
    content = await file.read()
    target_facility = facility_id or user.facility_id
    if target_facility is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="missing required facility context: supply facility_id or attach a facility to the user",
        )

    try:
        parsed = parse_workbook(content, filename=file.filename or "excel-upload")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if not detect_electricity_workbook(parsed):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{parsed.filename}: not recognized as an electricity workbook",
        )

    try:
        normalized = normalize_workbook(parsed)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    raw_lookup = dict(zip(parsed.headers, parsed.raw_headers))
    rows: list[tuple[object, ActivityRecordCreate, str]] = []
    errors: list[str] = []
    for record in normalized:
        quantity, unit, source_col = select_activity_quantity(record)
        if quantity is None:
            errors.append(f"row {record.source_row}: no mapped activity quantity available")
            continue
        try:
            payload = ActivityRecordCreate.model_validate(
                {
                    "facility_id": target_facility,
                    "period_start": datetime.combine(record.period_start, time.min),
                    "period_end": datetime.combine(record.period_end, time.min),
                    "activity_type": "electricity",
                    "quantity": quantity,
                    "unit": unit,
                    "source": "excel",
                    "confirmed_by_user": False,
                }
            )
        except ValidationError as exc:
            errors.append(f"row {record.source_row}: {_validation_error_message(exc)}")
            continue
        rows.append((record, payload, raw_lookup.get(source_col, source_col or "")))
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="; ".join(errors),
        )

    # Idempotent re-uploads: never create a draft for a row already ingested.
    new_rows = [
        row for row in rows if not _draft_exists(db, row[1], source_type="excel")
    ]

    drafts = [
        OCRDraft(
            user_id=user.id,
            source_filename=file.filename or "excel-upload",
            source_type="excel",
            source_row=record.source_row,
            source_column=source_column,
            facility_id=payload.facility_id,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        for record, payload, source_column in new_rows
    ]
    db.add_all(drafts)
    db.commit()
    for draft in drafts:
        db.refresh(draft)
    return drafts


@router.post(
    "/ocr/{draft_id}/confirm",
    response_model=ActivityRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_ocr_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> ActivityRecord:
    draft = db.get(OCRDraft, draft_id)
    if draft is None or (draft.user_id != user.id and user.role.name != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR draft not found")
    if draft.activity_record_id is not None or draft.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="OCR draft already confirmed")

    record = ActivityRecord(
        facility_id=draft.facility_id,
        period_start=draft.period_start,
        period_end=draft.period_end,
        activity_type=draft.activity_type,
        quantity=draft.quantity,
        unit=draft.unit,
        # Defaults to OCR for drafts that predate source_type tagging.
        source=draft.source_type or "ocr",
        confirmed_by_user=True,
    )
    db.add(record)
    db.flush()
    draft.activity_record_id = record.id
    draft.status = "confirmed"
    draft.confirmed_at = datetime.now(UTC)
    db.commit()
    db.refresh(record)
    return record
