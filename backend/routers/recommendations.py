"""Recommendations router — expose rule-engine outputs per facility/period."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_recommendations() -> dict:
    # TODO: implement GET /?facility_id=&period_id= and POST /evaluate to trigger rule engine
    return {"status": "not implemented"}
