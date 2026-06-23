"""ESG PDF report generation and download."""

from fastapi import APIRouter, Depends, Response

from dependencies import get_current_user
from models.user import User
from services.report import generate_esg_pdf

router = APIRouter()


@router.get("/esg")
def esg_report(_user: User = Depends(get_current_user)) -> Response:
    return Response(
        content=generate_esg_pdf(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="carbontrace-esg-report.pdf"'},
    )
