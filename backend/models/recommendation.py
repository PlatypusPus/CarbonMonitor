"""Recommendation — a rule-engine output tied to a facility and reporting period."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: FK to facilities.id
    period_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    # TODO: define what period_id refers to once the Period model/table is decided
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # TODO: enumerate rule_id values to match services/recommendations.py rule names
    message: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_numbers: Mapped[str | None] = mapped_column(Text)
    # JSON string — use json.loads/dumps at the service layer; no ORM JSON type for portability
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
