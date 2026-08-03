"""Features 5 + 6 — the adaptive interview loop.

The loop is NOT question -> answer -> question. It is:

    question -> answer -> evaluation -> decision -> {follow-up | hint | next | end}

The model proposes the next move; this module *enforces* the rules (max consecutive
follow-ups, no hint-after-hint, question budget, minimum length) so a hallucinated
decision can never derail or prematurely end a session.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai import AIProviderError, get_ai_provider
from app.evaluation.service import average_scores, evaluate_answer
from app.models.enums import InterviewStatus, TurnKind
from app.models.interview import Interview, InterviewTurn
from app.prompts.interviewer import (
    DECISION_SYSTEM,
    decision_user_prompt,
    interviewer_system,
    question_user_prompt,
)
from app.schemas.evaluation import AnswerEvaluation, GeneratedQuestion, InterviewerDecision

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_FOLLOW_UPS = 2
MIN_QUESTIONS_BEFORE_END = 2

FALLBACK_QUESTION = GeneratedQuestion(
    question=(
        "Walk me through a project you are proud of: what you built, the hardest technical "
        "decision you made, and what you would change now."
    ),
    skill_tag="general",
    difficulty="medium",
    expected_points=[
        "Describes the system concretely",
        "Explains a real trade-off",
        "Reflects on what they would improve",
    ],
    rationale="Fallback question used when generation is unavailable.",
)


@dataclass
class TurnOutcome:
    """What happened after the candidate answered."""

    evaluation: AnswerEvaluation
    action: str
    message: str
    next_turn: InterviewTurn | None
    finished: bool


class InterviewEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = get_ai_provider()

    # ------------------------------------------------------------------ helpers

    def _system_prompt(self, interview: Interview) -> str:
        return interviewer_system(
            mode=interview.mode,
            role=interview.role,
            company=interview.company,
            difficulty=interview.difficulty,
        )

    @staticmethod
    def _asked_questions(interview: Interview) -> list[str]:
        return [t.question for t in interview.turns if t.kind == TurnKind.QUESTION]

    @staticmethod
    def _consecutive_follow_ups(interview: Interview) -> int:
        count = 0
        for turn in reversed(interview.turns):
            if turn.kind == TurnKind.FOLLOW_UP:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _last_kind(interview: Interview) -> str:
        return interview.turns[-1].kind if interview.turns else ""

    def _next_sequence(self, interview: Interview) -> int:
        return len(interview.turns) + 1

    # ------------------------------------------------------------ question stage

    async def _generate_question(self, interview: Interview) -> GeneratedQuestion:
        context = interview.context or {}
        try:
            return await self.provider.structured(
                system=self._system_prompt(interview),
                user=question_user_prompt(
                    resume=context.get("resume"),
                    job=context.get("job"),
                    focus_skills=interview.focus_skills or [],
                    asked_so_far=self._asked_questions(interview),
                    question_number=interview.questions_asked + 1,
                    total_questions=interview.planned_questions,
                ),
                schema=GeneratedQuestion,
            )
        except AIProviderError:
            logger.exception("Question generation failed for interview %s", interview.id)
            return FALLBACK_QUESTION.model_copy()

    def _append_turn(
        self,
        interview: Interview,
        *,
        kind: str,
        question: str,
        skill_tag: str | None,
        expected_points: list[str] | None,
        parent_turn_id: str | None = None,
        meta: dict | None = None,
    ) -> InterviewTurn:
        turn = InterviewTurn(
            interview_id=interview.id,
            sequence=self._next_sequence(interview),
            kind=kind,
            question=question,
            skill_tag=skill_tag,
            expected_points=expected_points,
            parent_turn_id=parent_turn_id,
            question_meta=meta,
        )
        self.db.add(turn)
        interview.turns.append(turn)
        if kind == TurnKind.QUESTION:
            interview.questions_asked += 1
        return turn

    async def start(self, interview: Interview) -> InterviewTurn:
        """Emit the opening question and mark the interview live."""
        if interview.turns:
            return interview.turns[-1]

        generated = await self._generate_question(interview)
        turn = self._append_turn(
            interview,
            kind=TurnKind.QUESTION,
            question=generated.question,
            skill_tag=generated.skill_tag,
            expected_points=generated.expected_points,
            meta={"difficulty": generated.difficulty, "rationale": generated.rationale},
        )
        interview.status = InterviewStatus.IN_PROGRESS
        interview.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(turn)
        return turn

    # ------------------------------------------------------------ decision stage

    async def _decide(
        self, interview: Interview, turn: InterviewTurn, evaluation: AnswerEvaluation
    ) -> InterviewerDecision:
        try:
            decision = await self.provider.structured(
                system=DECISION_SYSTEM,
                user=decision_user_prompt(
                    question=turn.question,
                    answer=turn.answer or "",
                    evaluation=evaluation.model_dump(),
                    consecutive_follow_ups=self._consecutive_follow_ups(interview),
                    last_action=self._last_kind(interview),
                    questions_asked=interview.questions_asked,
                    planned_questions=interview.planned_questions,
                ),
                schema=InterviewerDecision,
                fast=True,
            )
        except AIProviderError:
            logger.exception("Decision failed for interview %s", interview.id)
            decision = InterviewerDecision(
                action="next", reason="decision unavailable", message="", skill_tag=""
            )
        return self._enforce_rules(interview, decision)

    def _enforce_rules(
        self, interview: Interview, decision: InterviewerDecision
    ) -> InterviewerDecision:
        """Server-side guardrails. The model advises; these rules decide."""
        action = decision.action if decision.action in {"follow_up", "hint", "next", "end"} else "next"

        if action == "follow_up":
            if self._consecutive_follow_ups(interview) >= MAX_CONSECUTIVE_FOLLOW_UPS:
                action = "next"
            elif not decision.message.strip():
                action = "next"

        if action == "hint":
            # A hint straight after a hint just stalls the room.
            if self._last_kind(interview) == TurnKind.HINT or not decision.message.strip():
                action = "next"

        if action == "end" and interview.questions_asked < MIN_QUESTIONS_BEFORE_END:
            action = "next"

        if action == "next" and interview.questions_asked >= interview.planned_questions:
            action = "end"

        if action != decision.action:
            logger.debug(
                "Overrode decision %s -> %s for interview %s",
                decision.action,
                action,
                interview.id,
            )
        return decision.model_copy(
            update={"action": action, "message": decision.message if action in {"follow_up", "hint"} else ""}
        )

    # -------------------------------------------------------------- answer stage

    async def submit_answer(
        self,
        interview: Interview,
        turn: InterviewTurn,
        answer: str,
        *,
        duration_seconds: float | None = None,
    ) -> TurnOutcome:
        turn.answer = answer
        turn.answered_at = datetime.now(timezone.utc)
        turn.answer_duration_seconds = duration_seconds

        evaluation = await evaluate_answer(interview=interview, turn=turn, answer=answer)
        turn.evaluation = evaluation.model_dump()
        turn.overall_score = float(evaluation.overall)
        self.db.commit()

        decision = await self._decide(interview, turn, evaluation)
        next_turn: InterviewTurn | None = None
        finished = False

        if decision.action == "follow_up":
            next_turn = self._append_turn(
                interview,
                kind=TurnKind.FOLLOW_UP,
                question=decision.message,
                skill_tag=turn.skill_tag,
                expected_points=turn.expected_points,
                parent_turn_id=turn.id,
                meta={"reason": decision.reason},
            )
        elif decision.action == "hint":
            next_turn = self._append_turn(
                interview,
                kind=TurnKind.HINT,
                question=decision.message,
                skill_tag=turn.skill_tag,
                expected_points=turn.expected_points,
                parent_turn_id=turn.id,
                meta={"reason": decision.reason},
            )
        elif decision.action == "next":
            generated = await self._generate_question(interview)
            next_turn = self._append_turn(
                interview,
                kind=TurnKind.QUESTION,
                question=generated.question,
                skill_tag=generated.skill_tag,
                expected_points=generated.expected_points,
                meta={"difficulty": generated.difficulty, "rationale": generated.rationale},
            )
        else:  # end
            finished = True
            self.complete(interview)

        self.db.commit()
        if next_turn is not None:
            self.db.refresh(next_turn)

        return TurnOutcome(
            evaluation=evaluation,
            action=decision.action,
            message=decision.message,
            next_turn=next_turn,
            finished=finished,
        )

    # ------------------------------------------------------------------- closing

    def complete(self, interview: Interview) -> None:
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.now(timezone.utc)
        averages = average_scores(interview.turns)
        interview.overall_score = averages.get("overall") or None
        self.db.commit()

    def current_turn(self, interview: Interview) -> InterviewTurn | None:
        """The turn awaiting an answer, if any."""
        for turn in reversed(interview.turns):
            if turn.answer is None:
                return turn
        return None
