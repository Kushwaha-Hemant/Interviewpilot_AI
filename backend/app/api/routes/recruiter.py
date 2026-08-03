"""Feature 15 — recruiter creates a shareable interview link and reads the report."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth.dependencies import CurrentUser, DbSession
from app.interview.engine import InterviewEngine
from app.interview.service import create_interview
from app.models.interview import Interview
from app.models.recruiter import InterviewInvite
from app.schemas.api import InterviewCreate, InterviewDetail, InviteCreate, InviteOut

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


def _require_recruiter(user) -> None:
    if not user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not marked as a recruiter",
        )


@router.post("/invites", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def create_invite(payload: InviteCreate, user: CurrentUser, db: DbSession) -> InterviewInvite:
    _require_recruiter(user)
    invite = InterviewInvite(
        recruiter_id=user.id,
        token=secrets.token_urlsafe(24),
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        config=payload.config.model_dump(mode="json"),
        max_uses=payload.max_uses,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/invites", response_model=list[InviteOut])
def list_invites(user: CurrentUser, db: DbSession) -> list[InterviewInvite]:
    _require_recruiter(user)
    return list(
        db.scalars(
            select(InterviewInvite)
            .where(InterviewInvite.recruiter_id == user.id)
            .order_by(InterviewInvite.created_at.desc())
        )
    )


@router.post("/invites/{token}/claim", response_model=InterviewDetail)
async def claim_invite(token: str, user: CurrentUser, db: DbSession) -> Interview:
    """A candidate opens the shared link — spin up their interview from the config."""
    invite = db.scalar(select(InterviewInvite).where(InterviewInvite.token == token))
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite link")
    if invite.uses >= invite.max_uses:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="This invite has already been used"
        )

    interview = create_interview(
        db, user=user, payload=InterviewCreate.model_validate(invite.config)
    )
    await InterviewEngine(db).start(interview)

    invite.uses += 1
    invite.interview_id = interview.id
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/invites/{invite_id}/interview", response_model=InterviewDetail)
def invite_interview(invite_id: str, user: CurrentUser, db: DbSession) -> Interview:
    """Recruiter reads the candidate's session (and its report, via /interviews/...)."""
    _require_recruiter(user)
    invite = db.get(InterviewInvite, invite_id)
    if invite is None or invite.recruiter_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.interview_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The candidate has not started yet"
        )
    interview = db.scalar(
        select(Interview)
        .options(selectinload(Interview.turns))
        .where(Interview.id == invite.interview_id)
    )
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview
