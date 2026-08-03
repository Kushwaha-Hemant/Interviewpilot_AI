"""Feature 9 — score a single answer with a dedicated evaluator prompt + schema."""

from __future__ import annotations

import logging

from app.ai import AIProviderError, get_ai_provider
from app.models.interview import Interview, InterviewTurn
from app.prompts.evaluator import EVALUATOR_SYSTEM, evaluator_user_prompt
from app.schemas.evaluation import AnswerEvaluation

logger = logging.getLogger(__name__)

# Used when the model is unreachable, so an interview never dies mid-session.
FALLBACK = AnswerEvaluation(
    technical_score=0,
    communication=0,
    confidence=0,
    grammar=0,
    clarity=0,
    overall=0,
    feedback="This answer could not be scored automatically. It has been recorded.",
    covered_points=[],
    missed_points=[],
    red_flags=[],
)


async def evaluate_answer(
    *, interview: Interview, turn: InterviewTurn, answer: str
) -> AnswerEvaluation:
    provider = get_ai_provider()
    try:
        return await provider.structured(
            system=EVALUATOR_SYSTEM,
            user=evaluator_user_prompt(
                question=turn.question,
                answer=answer,
                expected_points=turn.expected_points or [],
                skill_tag=turn.skill_tag or "",
                mode=interview.mode,
                role=interview.role,
            ),
            schema=AnswerEvaluation,
            fast=True,  # evaluation runs on every turn — keep it cheap and quick
        )
    except AIProviderError:
        logger.exception("Evaluation failed for turn %s", turn.id)
        return FALLBACK.model_copy()


def average_scores(turns: list[InterviewTurn]) -> dict[str, float]:
    """Mean of each score dimension across answered turns."""
    dimensions = ("technical_score", "communication", "confidence", "grammar", "clarity", "overall")
    scored = [t.evaluation for t in turns if t.evaluation]
    if not scored:
        return {d: 0.0 for d in dimensions}
    return {
        d: round(sum(float(e.get(d, 0) or 0) for e in scored) / len(scored), 1)
        for d in dimensions
    }


def skill_averages(turns: list[InterviewTurn]) -> dict[str, tuple[float, int]]:
    """Per-skill mean score and attempt count, for radar charts and weak-topic lists."""
    buckets: dict[str, list[float]] = {}
    for turn in turns:
        if not turn.evaluation or not turn.skill_tag:
            continue
        buckets.setdefault(turn.skill_tag, []).append(
            float(turn.evaluation.get("overall", 0) or 0)
        )
    return {
        skill: (round(sum(scores) / len(scores), 1), len(scores))
        for skill, scores in buckets.items()
    }
