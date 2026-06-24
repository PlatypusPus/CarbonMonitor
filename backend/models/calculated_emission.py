"""CalculatedEmission — result of applying an EmissionFactor to an ActivityRecord."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CalculatedEmission(Base):
    __tablename__ = "calculated_emissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    activity_record_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: FK to activity_records.id
    scope: Mapped[int] = mapped_column(Integer, nullable=False)
    # TODO: enforce scope IN (1, 2) at DB level with a check constraint
    co2e_kg: Mapped[float] = mapped_column(Float, nullable=False)
    emission_factor_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: FK to emission_factors.id — store the factor used so results are reproducible
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
