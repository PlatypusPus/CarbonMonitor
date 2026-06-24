"""ActivityRecord model — a single measured activity input before emission calculation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

# TODO: keep this list in sync with EmissionFactor.activity_type
ACTIVITY_TYPES = ("electricity", "diesel", "petrol", "lpg")
SOURCES = ("manual", "csv", "ocr")


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: add FK constraint to facilities.id once migration is ready
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activity_type: Mapped[str] = mapped_column(
        Enum(*ACTIVITY_TYPES, name="activity_type_enum"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    # TODO: define canonical unit strings per activity_type (e.g. "kWh", "litres")
    source: Mapped[str] = mapped_column(
        Enum(*SOURCES, name="activity_source_enum"), nullable=False
    )
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # OCR-sourced records must stay confirmed_by_user=False until a human approves
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
