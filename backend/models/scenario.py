"""Scenario — a what-if simulation record. NEVER joined into real reporting queries."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

# ponytail: IMPORTANT — scenarios are sandbox data. Any query that aggregates real emissions
# MUST exclude this table. Do not add FK relations from here to calculated_emissions.


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: FK to facilities.id
    baseline_period_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: same period reference question as Recommendation.period_id
    modified_inputs: Mapped[str | None] = mapped_column(Text)
    # JSON string of overridden ActivityRecord fields used in this simulation
    result_co2e_kg: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
