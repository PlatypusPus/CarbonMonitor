"""Facilities router — CRUD for monitored sites."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_facilities() -> dict:
    # TODO: implement list, create, get, update for Facility
    return {"status": "not implemented"}
