"""Features 2 + 11 — dashboard stats, streaks, skill breakdowns and chart series."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai import AIProviderError, get_ai_provider
from app.auth.dependencies import CurrentUser, DbSession
from app.models.enums import InterviewStatus
from app.models.interview import Interview
from app.prompts.coach import INSIGHT_SYSTEM, insight_user_prompt
from app.schemas.api import DashboardOut, SkillStat, TimelinePoint
from app.schemas.coaching import DashboardInsight

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

STRONG_THRESHOLD = 75
MIN_ATTEMPTS_FOR_SIGNAL = 1


def _practice_streak(dates: set[date]) -> int:
    """Consecutive days of practice ending today (or yesterday, so a day isn't lost
    the moment midnight passes)."""
    if not dates:
        return 0
    today = datetime.now().date()
    cursor = today if today in dates else today - timedelta(days=1)
    if cursor not in dates:
        return 0
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


@router.get("", response_model=DashboardOut)
async def get_dashboard(user: CurrentUser, db: DbSession) -> DashboardOut:
    interviews = list(
        db.scalars(
            select(Interview)
            .options(selectinload(Interview.turns))
            .where(Interview.user_id == user.id)
            .order_by(Interview.created_at.asc())
        )
    )

    completed = [i for i in interviews if i.status == InterviewStatus.COMPLETED]
    scored = [i for i in completed if i.overall_score is not None]
    average = round(sum(i.overall_score for i in scored) / len(scored), 1) if scored else None

    # --- per-skill aggregation across every answered turn
    buckets: dict[str, list[float]] = {}
    for interview in interviews:
        for turn in interview.turns:
            if turn.overall_score is None or not turn.skill_tag:
                continue
            buckets.setdefault(turn.skill_tag, []).append(turn.overall_score)

    stats = [
        SkillStat(
            skill=skill,
            score=round(sum(scores) / len(scores), 1),
            attempts=len(scores),
        )
        for skill, scores in buckets.items()
        if len(scores) >= MIN_ATTEMPTS_FOR_SIGNAL
    ]
    strong = sorted(
        [s for s in stats if s.score >= STRONG_THRESHOLD], key=lambda s: s.score, reverse=True
    )[:5]
    weak = sorted([s for s in stats if s.score < STRONG_THRESHOLD], key=lambda s: s.score)[:5]

    timeline = [
        TimelinePoint(
            date=i.completed_at or i.created_at,
            score=i.overall_score,
            mode=i.mode,
            interview_id=i.id,
        )
        for i in scored
    ]

    confidence_trend = []
    for interview in completed:
        values = [
            float(t.evaluation.get("confidence", 0) or 0)
            for t in interview.turns
            if t.evaluation
        ]
        if values:
            confidence_trend.append(
                TimelinePoint(
                    date=interview.completed_at or interview.created_at,
                    score=round(sum(values) / len(values), 1),
                    mode=interview.mode,
                    interview_id=interview.id,
                )
            )

    streak = _practice_streak({i.created_at.date() for i in interviews})

    recommendation: str | None = None
    focus_skill: str | None = None
    if stats:
        try:
            insight = await get_ai_provider().structured(
                system=INSIGHT_SYSTEM,
                user=insight_user_prompt(
                    stats={
                        "total_interviews": len(interviews),
                        "average_score": average,
                        "practice_streak_days": streak,
                        "strong_skills": [s.model_dump() for s in strong],
                        "weak_skills": [s.model_dump() for s in weak],
                        "recent_modes": [i.mode for i in interviews[-5:]],
                    }
                ),
                schema=DashboardInsight,
                fast=True,
            )
            recommendation = insight.recommendation
            focus_skill = insight.focus_skill
        except AIProviderError:
            logger.warning("Dashboard insight unavailable", exc_info=True)
            if weak:
                recommendation = f"Run a focused mock on {weak[0].skill} — it is your lowest-scoring topic."
                focus_skill = weak[0].skill

    return DashboardOut(
        total_interviews=len(interviews),
        completed_interviews=len(completed),
        average_score=average,
        practice_streak_days=streak,
        strong_skills=strong,
        weak_skills=weak,
        timeline=timeline,
        confidence_trend=confidence_trend,
        ai_recommendation=recommendation,
        focus_skill=focus_skill,
    )
