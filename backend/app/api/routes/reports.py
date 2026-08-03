"""Features 10 + 12 — report generation, retrieval and PDF export."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth.dependencies import CurrentUser, DbSession
from app.models.enums import InterviewStatus
from app.models.interview import Interview
from app.reports.pdf import render_report_pdf
from app.reports.service import generate_report
from app.schemas.api import ReportOut

router = APIRouter(prefix="/interviews", tags=["reports"])


def _load(db, interview_id: str, user_id: str) -> Interview:
    interview = db.scalar(
        select(Interview)
        .options(selectinload(Interview.turns))
        .where(Interview.id == interview_id)
    )
    if interview is None or interview.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview


@router.post("/{interview_id}/report", response_model=ReportOut)
async def create_report(interview_id: str, user: CurrentUser, db: DbSession):
    interview = _load(db, interview_id, user.id)
    if not any(t.evaluation for t in interview.turns):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Answer at least one question before generating a report",
        )
    if interview.status != InterviewStatus.COMPLETED:
        from app.interview.engine import InterviewEngine

        InterviewEngine(db).complete(interview)
    return await generate_report(db, interview)


@router.get("/{interview_id}/report", response_model=ReportOut)
def get_report(interview_id: str, user: CurrentUser, db: DbSession):
    interview = _load(db, interview_id, user.id)
    if interview.report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report yet — POST to this URL to generate one",
        )
    return interview.report


@router.get("/{interview_id}/report.pdf")
def download_report_pdf(interview_id: str, user: CurrentUser, db: DbSession) -> Response:
    interview = _load(db, interview_id, user.id)
    if interview.report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Generate the report first"
        )
    pdf = render_report_pdf(interview, interview.report)
    filename = f"interviewpilot-{interview.role.replace(' ', '-').lower()}-{interview.id[:8]}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
