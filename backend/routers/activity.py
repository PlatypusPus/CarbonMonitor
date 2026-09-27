"""Activity records router — ingest and manage ActivityRecord entries."""

from datetime import UTC, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import check_facility_access, get_current_user, require_role
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.facility import Facility
from models.ocr_draft import OCRDraft
from models.user import User
from schemas.activity_record import ActivityRecordCreate, ActivityRecordResponse
from schemas.ocr_draft import OCRDraftResponse
from services.drafts import (
    SOURCE_TYPE_EXCEL,
    SOURCE_TYPE_OCR,
    activity_source_for_draft,
    build_draft,
    draft_exists,
)
from services.excel.detector import detect_electricity_workbook
from services.excel.normalizer import normalize_workbook, select_activity_quantity
from services.excel.parser import parse_workbook
from services.factors import resolve_factor
from services.ocr import extract_activities_from_document

router = APIRouter()


@router.get("", response_model=list[ActivityRecordResponse])
def list_activity_records(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    facility_id: UUID | None = None,
    confirmed_only: bool = True,
) -> list[ActivityRecord]:
    """List activity records (emissions ledger entries).

    By default returns only confirmed records. Use confirmed_only=false to include drafts.
    Non-admin users only see records for their assigned facility.
    """
    query = db.query(ActivityRecord)
    if user.role.name != "admin":
        query = query.filter(ActivityRecord.facility_id == user.facility_id)
    if facility_id is not None:
        check_facility_access(user, facility_id)
        query = query.filter(ActivityRecord.facility_id == facility_id)
    if confirmed_only:
        query = query.filter(ActivityRecord.confirmed_by_user.is_(True))
    return query.order_by(ActivityRecord.period_start.desc()).all()


@router.get("/drafts", response_model=list[OCRDraftResponse])
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
    facility_id: UUID | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> list[OCRDraft]:
    """Stage a scanned/tabular document as reviewable drafts.

    ``facility_id`` is the facility picked in the intake UI. When supplied it
    wins over whatever facility the document names, and it doubles as the
    fallback for documents that name none — so a bill without a facility label
    still stages instead of failing validation.
    """
    content = await file.read()
    try:
        extracted = extract_activities_from_document(
            content, file.filename, str(facility_id) if facility_id else None
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Determine effective facility_id for each record and validate access
    payloads = []
    for record in extracted:
        # Priority: form facility_id > document facility_id > user's facility_id
        record_facility_id = record.get("facility_id")
        effective_facility_id = facility_id or record_facility_id
        if effective_facility_id is None:
            effective_facility_id = user.facility_id
        if effective_facility_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="missing required facility context: supply facility_id, include it in the document, or attach a facility to the user",
            )
        # Enforce scope check on the effective facility
        if user.role.name != "admin":
            if user.facility_id is None or user.facility_id != effective_facility_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this facility",
                )
        payloads.append(
            ActivityRecordCreate.model_validate(
                {
                    **record,
                    "facility_id": str(effective_facility_id),
                    "source": "ocr",
                    "confirmed_by_user": False,
                }
            )
        )

    # Idempotent re-uploads: never create a draft for a row already ingested.
    payloads = _filter_new_drafts(db, payloads, source_type=SOURCE_TYPE_OCR)

    drafts: list[OCRDraft] = []
    for payload in payloads:
        draft = build_draft(
            user_id=user.id,
            facility_id=payload.facility_id,
            source_filename=file.filename or "ocr-upload",
            source_type=SOURCE_TYPE_OCR,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        try:
            db.add(draft)
            db.commit()
            db.refresh(draft)
            drafts.append(draft)
        except IntegrityError:
            db.rollback()
            # Unique constraint violated — concurrent upload already inserted this draft key. Skip.
            continue
    return drafts


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
    # Enforce scope check on the selected facility
    if facility_id is not None:
        check_facility_access(user, facility_id)
    elif user.role.name != "admin" and user.facility_id != target_facility:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this facility",
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
        row
        for row in rows
        if not draft_exists(
            db,
            facility_id=row[1].facility_id,
            period_start=row[1].period_start,
            period_end=row[1].period_end,
            activity_type=row[1].activity_type,
            quantity=row[1].quantity,
            unit=row[1].unit,
            source_type=SOURCE_TYPE_EXCEL,
        )
    ]

    drafts: list[OCRDraft] = []
    for record, payload, source_column in new_rows:
        draft = build_draft(
            user_id=user.id,
            facility_id=payload.facility_id,
            source_filename=file.filename or "excel-upload",
            source_type=SOURCE_TYPE_EXCEL,
            source_row=record.source_row,
            source_column=source_column,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        try:
            db.add(draft)
            db.commit()
            db.refresh(draft)
            drafts.append(draft)
        except IntegrityError:
            db.rollback()
            # Unique constraint violated — concurrent upload already inserted this draft key. Skip.
            continue
    return drafts


def _validation_error_message(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )


def _filter_new_drafts(
    db: Session, payloads: list[ActivityRecordCreate], source_type: str
) -> list[ActivityRecordCreate]:
    """Drop payloads that already exist as drafts (idempotent re-uploads)."""
    return [
        payload
        for payload in payloads
        if not draft_exists(
            db,
            facility_id=payload.facility_id,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
            source_type=source_type,
        )
    ]


@router.get("/{record_id}", response_model=ActivityRecordResponse)
def get_activity_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityRecord:
    """Get a single activity record by ID."""
    record = db.get(ActivityRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity record not found")
    if user.role.name != "admin" and record.facility_id != user.facility_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this record")
    return record


@router.post("", response_model=ActivityRecordResponse, status_code=status.HTTP_201_CREATED)
def create_activity_record(
    payload: ActivityRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> ActivityRecord:
    """Create an activity record directly (bypasses draft review).

    Only for admin/facility_manager. Record is immediately confirmed and credited to emissions.
    """
    if user.role.name != "admin":
        check_facility_access(user, payload.facility_id)
    record = ActivityRecord(
        facility_id=payload.facility_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        activity_type=payload.activity_type,
        quantity=payload.quantity,
        unit=payload.unit,
        source=payload.source,
        confirmed_by_user=True,
    )
    db.add(record)
    db.flush()

    facility = db.get(Facility, record.facility_id)
    factor = resolve_factor(
        db,
        record.activity_type,
        record.period_end,
        region_code=facility.region_code if facility else None,
    )
    if factor is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"no emission factor for activity type '{record.activity_type}'",
        )
    from services.calculation import calculate_emissions
    calc = calculate_emissions(record, factor)
    db.add(calc)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{record_id}", response_model=ActivityRecordResponse)
def update_activity_record(
    record_id: UUID,
    payload: ActivityRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> ActivityRecord:
    """Update an activity record (admin only).

    Recalculates emission if quantity/activity_type/period changes.
    """
    record = db.get(ActivityRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity record not found")
    if user.role.name != "admin":
        check_facility_access(user, record.facility_id)
        check_facility_access(user, payload.facility_id)

    # Update fields
    record.facility_id = payload.facility_id
    record.period_start = payload.period_start
    record.period_end = payload.period_end
    record.activity_type = payload.activity_type
    record.quantity = payload.quantity
    record.unit = payload.unit
    record.source = payload.source

    # Recalculate emission
    db.query(CalculatedEmission).filter(CalculatedEmission.activity_record_id == record.id).delete(synchronize_session=False)
    facility = db.get(Facility, record.facility_id)
    factor = resolve_factor(
        db,
        record.activity_type,
        record.period_end,
        region_code=facility.region_code if facility else None,
    )
    if factor is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"no emission factor for activity type '{record.activity_type}'",
        )
    from services.calculation import calculate_emissions
    calc = calculate_emissions(record, factor)
    db.add(calc)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> Response:
    """Delete an activity record and its emission (admin only)."""
    record = db.get(ActivityRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity record not found")
    db.query(CalculatedEmission).filter(CalculatedEmission.activity_record_id == record.id).delete(synchronize_session=False)
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/drafts", response_model=list[OCRDraftResponse])
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
    facility_id: UUID | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> list[OCRDraft]:
    """Stage a scanned/tabular document as reviewable drafts.

    ``facility_id`` is the facility picked in the intake UI. When supplied it
    wins over whatever facility the document names, and it doubles as the
    fallback for documents that name none — so a bill without a facility label
    still stages instead of failing validation.
    """
    content = await file.read()
    try:
        extracted = extract_activities_from_document(
            content, file.filename, str(facility_id) if facility_id else None
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Determine effective facility_id for each record and validate access
    payloads = []
    for record in extracted:
        # Priority: form facility_id > document facility_id > user's facility_id
        record_facility_id = record.get("facility_id")
        effective_facility_id = facility_id or record_facility_id
        if effective_facility_id is None:
            effective_facility_id = user.facility_id
        if effective_facility_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="missing required facility context: supply facility_id, include it in the document, or attach a facility to the user",
            )
        # Enforce scope check on the effective facility
        if user.role.name != "admin":
            if user.facility_id is None or user.facility_id != effective_facility_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this facility",
                )
        payloads.append(
            ActivityRecordCreate.model_validate(
                {
                    **record,
                    "facility_id": str(effective_facility_id),
                    "source": "ocr",
                    "confirmed_by_user": False,
                }
            )
        )

    # Idempotent re-uploads: never create a draft for a row already ingested.
    payloads = _filter_new_drafts(db, payloads, source_type=SOURCE_TYPE_OCR)

    drafts: list[OCRDraft] = []
    for payload in payloads:
        draft = build_draft(
            user_id=user.id,
            facility_id=payload.facility_id,
            source_filename=file.filename or "ocr-upload",
            source_type=SOURCE_TYPE_OCR,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        try:
            db.add(draft)
            db.commit()
            db.refresh(draft)
            drafts.append(draft)
        except IntegrityError:
            db.rollback()
            # Unique constraint violated — concurrent upload already inserted this draft key. Skip.
            continue
    return drafts


def _validation_error_message(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )


def _filter_new_drafts(
    db: Session, payloads: list[ActivityRecordCreate], source_type: str
) -> list[ActivityRecordCreate]:
    """Drop payloads that already exist as drafts (idempotent re-uploads)."""
    return [
        payload
        for payload in payloads
        if not draft_exists(
            db,
            facility_id=payload.facility_id,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
            source_type=source_type,
        )
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
    # Enforce scope check on the selected facility
    if facility_id is not None:
        check_facility_access(user, facility_id)
    elif user.role.name != "admin" and user.facility_id != target_facility:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this facility",
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
        row
        for row in rows
        if not draft_exists(
            db,
            facility_id=row[1].facility_id,
            period_start=row[1].period_start,
            period_end=row[1].period_end,
            activity_type=row[1].activity_type,
            quantity=row[1].quantity,
            unit=row[1].unit,
            source_type=SOURCE_TYPE_EXCEL,
        )
    ]

    drafts: list[OCRDraft] = []
    for record, payload, source_column in new_rows:
        draft = build_draft(
            user_id=user.id,
            facility_id=payload.facility_id,
            source_filename=file.filename or "excel-upload",
            source_type=SOURCE_TYPE_EXCEL,
            source_row=record.source_row,
            source_column=source_column,
            period_start=payload.period_start,
            period_end=payload.period_end,
            activity_type=payload.activity_type,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        try:
            db.add(draft)
            db.commit()
            db.refresh(draft)
            drafts.append(draft)
        except IntegrityError:
            db.rollback()
            # Unique constraint violated — concurrent upload already inserted this draft key. Skip.
            continue
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
    """Confirm a staged draft, crediting it to the emissions ledger.

    This is the single gate through which reviewed data reaches
    ``activity_records`` and ``calculated_emissions``. A draft that already has
    a linked record (rows staged by an older upload build wrote straight to the
    ledger) adopts that record instead of creating a duplicate, so historical
    data can be reviewed in place rather than re-ingested.

    Uses SELECT FOR UPDATE to prevent concurrent confirmations from creating duplicate ledger records.
    """
    # Lock the draft row to prevent concurrent confirmations
    draft = db.query(OCRDraft).filter(OCRDraft.id == draft_id).with_for_update().first()
    if draft is None or (draft.user_id != user.id and user.role.name != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR draft not found")

    # Enforce facility access on the draft's facility
    if user.role.name != "admin":
        check_facility_access(user, draft.facility_id)

    if draft.status == "confirmed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="OCR draft already confirmed")

    # Atomically transition status to prevent race window
    draft.status = "confirmed"
    draft.confirmed_at = datetime.now(UTC)

    if draft.activity_record_id is not None:
        record = db.get(ActivityRecord, draft.activity_record_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="linked activity record is missing; re-upload this file",
            )
        record.confirmed_by_user = True
    else:
        record = ActivityRecord(
            facility_id=draft.facility_id,
            period_start=draft.period_start,
            period_end=draft.period_end,
            activity_type=draft.activity_type,
            quantity=draft.quantity,
            unit=draft.unit,
            # "upload" drafts are recorded as "csv" in the ledger's source enum.
            source=activity_source_for_draft(draft.source_type or SOURCE_TYPE_OCR),
            confirmed_by_user=True,
        )
        db.add(record)
        db.flush()

    _credit_emission(db, record)
    draft.activity_record_id = record.id
    db.commit()
    db.refresh(record)
    return record


@router.delete("/ocr/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def reject_ocr_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> Response:
    """Discard a draft that should not be ingested.

    Confirmed drafts are immutable — the ledger is append-only for audit, so a
    confirmed row is corrected by uploading a replacement, not by deleting it.
    Discarding a draft that adopted a pre-existing unconfirmed record also
    removes that record and its emissions, which is how duplicate rows staged
    by the old upload path get cleaned up.

    Uses SELECT FOR UPDATE to prevent concurrent operations.
    """
    # Lock the draft row to prevent concurrent operations
    draft = db.query(OCRDraft).filter(OCRDraft.id == draft_id).with_for_update().first()
    if draft is None or (draft.user_id != user.id and user.role.name != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR draft not found")

    # Enforce facility access on the draft's facility
    if user.role.name != "admin":
        check_facility_access(user, draft.facility_id)

    if draft.status == "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="confirmed drafts cannot be discarded",
        )

    if draft.activity_record_id is not None:
        record = db.get(ActivityRecord, draft.activity_record_id)
        if record is not None and not record.confirmed_by_user:
            db.query(CalculatedEmission).filter(
                CalculatedEmission.activity_record_id == record.id
            ).delete(synchronize_session=False)
            db.delete(record)

    db.delete(draft)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _credit_emission(db: Session, record: ActivityRecord) -> CalculatedEmission:
    """Apply the matching emission factor to a confirmed record.

    Reuses an existing calculation when one is already present so confirming a
    legacy draft cannot double-count.
    """
    existing = (
        db.query(CalculatedEmission)
        .filter(CalculatedEmission.activity_record_id == record.id)
        .first()
    )
    if existing is not None:
        return existing

    facility = db.get(Facility, record.facility_id)
    factor = resolve_factor(
        db,
        record.activity_type,
        record.period_end,
        region_code=facility.region_code if facility else None,
    )
    if factor is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"no emission factor for activity type '{record.activity_type}'",
        )

    from services.calculation import calculate_emissions

    calc = calculate_emissions(record, factor)
    db.add(calc)
    return calc
