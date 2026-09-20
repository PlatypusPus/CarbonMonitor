"""Activity records router — ingest and manage ActivityRecord entries."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.activity_record import ActivityRecord
from schemas.activity_record import ActivityRecordCreate, ActivityRecordResponse

router = APIRouter()


@router.post("/", response_model=ActivityRecordResponse, status_code=status.HTTP_201_CREATED)
def create_activity_record(record: ActivityRecordCreate, db: Session = Depends(get_db)) -> Any:
    db_record = ActivityRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/", response_model=list[ActivityRecordResponse])
def list_activity_records(
    skip: int = 0, limit: int = 100, facility_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> Any:
    stmt = select(ActivityRecord).offset(skip).limit(limit)
    if facility_id:
        stmt = stmt.where(ActivityRecord.facility_id == facility_id)
    records = db.execute(stmt).scalars().all()
    return records


@router.get("/{record_id}", response_model=ActivityRecordResponse)
def get_activity_record(record_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    record = db.get(ActivityRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="ActivityRecord not found")
    return record


@router.post("/{record_id}/confirm", response_model=ActivityRecordResponse)
def confirm_activity_record(record_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    record = db.get(ActivityRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="ActivityRecord not found")
    record.confirmed_by_user = True
    db.commit()
    db.refresh(record)
    return record
