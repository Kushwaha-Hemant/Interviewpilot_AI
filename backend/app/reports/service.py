"""Features 10 + 12 + 14 — build the post-interview report."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.ai import AIProviderError, get_ai_provider
from app.evaluation.service import average_scores, skill_averages
from app.models.interview import Interview
from app.models.report import InterviewReport
from app.prompts.coach import COACH_SYSTEM, coach_user_prompt
from app.schemas.coaching import CoachReport

logger = logging.getLogger(__name__)


def build_transcript(interview: Interview) -> list[dict]:
    return [
        {
            "sequence": turn.sequence,
            "kind": turn.kind,
            "skill": turn.skill_tag,
            "question": turn.question,
            "answer": turn.answer or "",
            "scores": turn.evaluation or {},
        }
        for turn in interview.turns
    ]


async def generate_report(db: Session, interview: Interview) -> InterviewReport:
    """Create or refresh the report for a finished interview."""
    averages = average_scores(interview.turns)
    provider = get_ai_provider()

    coach: CoachReport | None = None
    try:
        coach = await provider.structured(
            system=COACH_SYSTEM,
            user=coach_user_prompt(
                role=interview.role,
                mode=interview.mode,
                company=interview.company,
                transcript=build_transcript(interview),
                averages=averages,
            ),
            schema=CoachReport,
        )
    except AIProviderError:
        logger.exception("Coach report generation failed for interview %s", interview.id)

    report = interview.report or InterviewReport(interview_id=interview.id)

    report.technical_score = averages["technical_score"]
    report.communication_score = averages["communication"]
    report.confidence_score = averages["confidence"]
    report.grammar_score = averages["grammar"]
    report.clarity_score = averages["clarity"]
    report.overall_score = averages["overall"]

    if coach is not None:
        report.summary = coach.summary
        report.strengths = coach.strengths
        report.weaknesses = coach.weaknesses
        report.mistakes = [m.model_dump() for m in coach.mistakes]
        report.recommendations = [r.model_dump() for r in coach.recommendations]
        report.learning_plan = [s.model_dump() for s in coach.learning_plan]
        report.skill_breakdown = [s.model_dump() for s in coach.skill_breakdown]
        report.readiness_percent = float(coach.readiness_percent)
        report.readiness_role = coach.readiness_role
        report.estimated_prep_time = coach.estimated_prep_time
    else:
        # Degrade to computed-only: still a useful report, just no narrative coaching.
        report.summary = (
            "Automated coaching was unavailable for this session. Scores below are computed "
            "from the per-answer evaluations."
        )
        report.skill_breakdown = [
            {"skill": skill, "score": round(score)}
            for skill, (score, _) in skill_averages(interview.turns).items()
        ]
        report.readiness_role = interview.role

    if interview.report is None:
        db.add(report)
        interview.report = report
    db.commit()
    db.refresh(report)
    return report
