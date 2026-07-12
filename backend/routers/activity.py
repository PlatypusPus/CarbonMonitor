"""Activity records router — ingest and manage ActivityRecord entries."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.activity_record import ActivityRecord
from models.ocr_draft import OCRDraft
from models.user import User
from schemas.activity_record import ActivityRecordCreate, ActivityRecordResponse
from schemas.ocr_draft import OCRDraftResponse
from services.ocr import extract_activity_from_document

router = APIRouter()


@router.get("/")
def list_activity_records() -> dict:
    # TODO: implement create (manual + csv), list, get, confirm (for OCR drafts)
    return {"status": "not implemented"}


@router.post("/ocr", response_model=OCRDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_ocr_draft(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> OCRDraft:
    content = await file.read()
    try:
        extracted = extract_activity_from_document(content)
        payload = ActivityRecordCreate.model_validate(
            {**extracted, "source": "ocr", "confirmed_by_user": False}
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    draft = OCRDraft(
        user_id=user.id,
        source_filename=file.filename or "ocr-upload",
        facility_id=payload.facility_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        activity_type=payload.activity_type,
        quantity=payload.quantity,
        unit=payload.unit,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


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
        source="ocr",
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
