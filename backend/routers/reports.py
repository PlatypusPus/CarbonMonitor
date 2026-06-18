"""ESG PDF report generation and download."""

from elasticsearch import ConnectionError as ESConnectionError
from fastapi import APIRouter, Depends, HTTPException, Response, status

from dependencies import get_current_user
from models.user import User
from services.report import generate_esg_pdf

router = APIRouter()


@router.get("/esg")
def esg_report(_user: User = Depends(get_current_user)) -> Response:
    try:
        pdf = generate_esg_pdf()
    except ESConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch unavailable",
        ) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="carbontrace-esg-report.pdf"'},
    )
