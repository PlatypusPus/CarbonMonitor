"""ESG PDF report generation and download."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, facility_scope
from models.user import User
from services.report import generate_esg_pdf

router = APIRouter()


@router.get("/esg")
def esg_report(_user: User = Depends(get_current_user), db: Session = Depends(get_db),
               scope: UUID | None = Depends(facility_scope)) -> Response:
    return Response(
        content=generate_esg_pdf(db, facility_id=scope),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="carbontrace-esg-report.pdf"'},
    )
