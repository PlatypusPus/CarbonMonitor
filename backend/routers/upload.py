"""CSV/XLSX data uploads for cross-verification against API-sourced emissions."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.upload import Upload
from models.user import User
from schemas.upload import UploadResponse
from services.uploads import (
    convert_xlsx_to_csv_bytes,
    index_upload_readings,
    parse_emissions_csv,
)

router = APIRouter()


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "facility_manager")),
) -> Upload:
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

    record = Upload(
        user_id=user.id,
        facility_id=user.facility_id,
        filename=file.filename or "upload.csv",
        status="processing",
        row_count=len(rows),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        index_upload_readings(db, str(record.id), user.facility_id, rows)
    except Exception:
        record.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to index uploaded data",
        ) from None

    record.status = "completed"
    db.commit()
    db.refresh(record)
    return record
