"""Scenarios router — what-if simulation endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_scenarios() -> dict:
    # TODO: implement POST /run (calls services.scenario.run_scenario, persists to scenarios table)
    # and GET /{id} for past scenario results
    return {"status": "not implemented"}
