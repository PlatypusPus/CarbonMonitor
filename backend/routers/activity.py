"""Activity records router — ingest and manage ActivityRecord entries."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_activity_records() -> dict:
    # TODO: implement create (manual + csv), list, get, confirm (for OCR drafts)
    return {"status": "not implemented"}
