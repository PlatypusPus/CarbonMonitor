"""Calculations router — trigger emission calculation for activity records."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_calculations() -> dict:
    # TODO: implement POST /{activity_record_id}/calculate and GET for results
    return {"status": "not implemented"}
