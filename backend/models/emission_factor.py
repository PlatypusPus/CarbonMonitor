"""EmissionFactor — lookup table mapping activity type + region to a CO2e multiplier."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

# TODO: keep in sync with ActivityRecord.ACTIVITY_TYPES
ACTIVITY_TYPES = ("electricity", "diesel", "petrol", "lpg")


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    activity_type: Mapped[str] = mapped_column(
        Enum(*ACTIVITY_TYPES, name="ef_activity_type_enum"), nullable=False
    )
    # NULL region means factor applies globally (e.g. combustion fuels are region-independent)
    region: Mapped[str | None] = mapped_column(String(50))
    factor_value: Mapped[float] = mapped_column(Float, nullable=False)
    # TODO: populate factor_value from authoritative source (e.g. DEFRA, EPA) — do not guess values
    unit: Mapped[str] = mapped_column(String(100), nullable=False)
    # TODO: define unit convention, e.g. "kg CO2e / kWh"
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
