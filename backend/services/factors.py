"""Emission-factor lookup shared by the draft-confirmation and calculation paths.

Kept out of ``services.calculation`` on purpose: that module is the pure
calculation layer and is not allowed to touch the DB.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.emission_factor import EmissionFactor


def resolve_factor(
    db: Session,
    activity_type: str,
    period_end: datetime,
    region_code: str | None = None,
) -> EmissionFactor | None:
    """Return the best factor for an activity, or ``None`` when none applies.

    Prefers a factor scoped to the facility's region, falls back to the global
    (``region IS NULL``) factor, and only accepts factors whose validity window
    covers ``period_end``.
    """
    stmt = (
        select(EmissionFactor)
        .where(EmissionFactor.activity_type == activity_type)
        .where(
            or_(
                EmissionFactor.region == region_code,
                EmissionFactor.region.is_(None),
            )
        )
        .where(
            or_(
                EmissionFactor.valid_from <= period_end,
                EmissionFactor.valid_from.is_(None),
            )
        )
        .where(
            or_(
                EmissionFactor.valid_to >= period_end,
                EmissionFactor.valid_to.is_(None),
            )
        )
        .order_by(EmissionFactor.region.is_(None))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()
