"""Features 5/6/7/13 — interview lifecycle over REST.

The WebSocket in app/websocket/interview_ws.py is the primary transport for a live
session; these endpoints are the equivalent request/response fallback and are what the
dashboard/history screens read.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth.dependencies import CurrentUser, DbSession
from app.models.enums import COMPANY_STYLES, InterviewStatus
from app.models.interview import Interview
from app.interview.engine import InterviewEngine
from app.interview.service import create_interview
from app.schemas.api import (
    AnswerRequest,
    InterviewCreate,
    InterviewDetail,
    InterviewOut,
    TurnOut,
    TurnResult,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _load(db, interview_id: str, user_id: str) -> Interview:
    interview = db.scalar(
        select(Interview)
        .options(selectinload(Interview.turns))
        .where(Interview.id == interview_id)
    )
    if interview is None or interview.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview


@router.get("/companies", tags=["reference"])
def list_companies() -> list[dict[str, str]]:
    """Feature 13 — company modes the interviewer can imitate."""
    return [
        {"id": key, "label": key.replace("_", " ").title(), "style": value}
        for key, value in COMPANY_STYLES.items()
    ]


@router.post("", response_model=InterviewDetail, status_code=status.HTTP_201_CREATED)
async def create(payload: InterviewCreate, user: CurrentUser, db: DbSession) -> Interview:
    interview = create_interview(db, user=user, payload=payload)
    await InterviewEngine(db).start(interview)
    db.refresh(interview)
    return interview


@router.get("", response_model=list[InterviewOut])
def list_interviews(user: CurrentUser, db: DbSession, limit: int = 50) -> list[Interview]:
    return list(
        db.scalars(
            select(Interview)
            .where(Interview.user_id == user.id)
            .order_by(Interview.created_at.desc())
            .limit(min(limit, 200))
        )
    )


@router.get("/{interview_id}", response_model=InterviewDetail)
def get_interview(interview_id: str, user: CurrentUser, db: DbSession) -> Interview:
    return _load(db, interview_id, user.id)


@router.get("/{interview_id}/current-turn", response_model=TurnOut | None)
def current_turn(interview_id: str, user: CurrentUser, db: DbSession):
    interview = _load(db, interview_id, user.id)
    return InterviewEngine(db).current_turn(interview)


@router.post("/{interview_id}/answer", response_model=TurnResult)
async def answer(
    interview_id: str, payload: AnswerRequest, user: CurrentUser, db: DbSession
) -> TurnResult:
    interview = _load(db, interview_id, user.id)
    if interview.status == InterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This interview is already complete"
        )

    engine = InterviewEngine(db)
    turn = engine.current_turn(interview)
    if turn is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="There is no open question to answer"
        )

    outcome = await engine.submit_answer(
        interview, turn, payload.answer, duration_seconds=payload.duration_seconds
    )
    return TurnResult(
        evaluation=outcome.evaluation.model_dump(),
        action=outcome.action,
        message=outcome.message,
        next_turn=TurnOut.model_validate(outcome.next_turn) if outcome.next_turn else None,
        interview_status=InterviewStatus(interview.status),
    )


@router.post("/{interview_id}/finish", response_model=InterviewOut)
def finish(interview_id: str, user: CurrentUser, db: DbSession) -> Interview:
    """End early — the candidate chose to stop."""
    interview = _load(db, interview_id, user.id)
    if interview.status != InterviewStatus.COMPLETED:
        InterviewEngine(db).complete(interview)
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_interview(interview_id: str, user: CurrentUser, db: DbSession) -> None:
    interview = _load(db, interview_id, user.id)
    db.delete(interview)
    db.commit()
