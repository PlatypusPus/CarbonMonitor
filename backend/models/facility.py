"""Facility model representing a monitored site."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.upload import Upload
    from models.user import User

FACILITY_TYPES = ("office", "warehouse", "data_center", "manufacturing")


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    region_code: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    facility_type: Mapped[str | None] = mapped_column(
        Enum(*FACILITY_TYPES, name="facility_type_enum")
    )

    users: Mapped[list[User]] = relationship(back_populates="facility")
    uploads: Mapped[list[Upload]] = relationship(back_populates="facility")
