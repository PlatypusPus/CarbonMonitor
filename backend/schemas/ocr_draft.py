"""Request/response schemas for OCR drafts."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OCRDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_filename: str
    source_type: str = "ocr"
    source_row: int | None = None
    source_column: str | None = None
    facility_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    activity_type: str
    quantity: float
    unit: str
    status: str
    activity_record_id: uuid.UUID | None = None
    confirmed_at: datetime | None = None
    created_at: datetime
