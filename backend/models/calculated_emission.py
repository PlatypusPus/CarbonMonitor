"""CalculatedEmission — result of applying an EmissionFactor to an ActivityRecord."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CalculatedEmission(Base):
    __tablename__ = "calculated_emissions"
    __table_args__ = (
        CheckConstraint("scope IN (1, 2)", name="check_scope_1_2"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    activity_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_records.id"), nullable=False)
    scope: Mapped[int] = mapped_column(Integer, nullable=False)
    co2e_kg: Mapped[float] = mapped_column(Float, nullable=False)
    emission_factor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("emission_factors.id"), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
