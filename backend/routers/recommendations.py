"""Recommendations router — expose rule-engine outputs per facility/period."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, check_facility_access
from models.user import User
from models.recommendation import Recommendation
from schemas.recommendation import RecommendationResponse
from services.recommendations import evaluate_rules

router = APIRouter()


@router.get("/", response_model=list[RecommendationResponse])
def list_recommendations(
    facility_id: uuid.UUID | None = None,
    period_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    if facility_id:
        check_facility_access(current_user, facility_id)
    elif current_user.role.name != "admin":
        facility_id = current_user.facility_id

    stmt = select(Recommendation)
    if facility_id:
        stmt = stmt.where(Recommendation.facility_id == facility_id)
    if period_id:
        stmt = stmt.where(Recommendation.period_id == period_id)
    return db.execute(stmt).scalars().all()


@router.post("/evaluate", response_model=list[RecommendationResponse])
def run_evaluation(
    facility_id: uuid.UUID,
    period_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    check_facility_access(current_user, facility_id)
    recs = evaluate_rules(db, facility_id, period_id)
    for rec in recs:
        db.add(rec)
    db.commit()
    for rec in recs:
        db.refresh(rec)
    return recs
