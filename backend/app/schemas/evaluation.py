"""Structured Output schemas for the interview loop (features 5, 6, 9)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedQuestion(BaseModel):
    """Feature 5 — a dynamically generated interview question."""

    question: str
    skill_tag: str = Field(description="Primary skill this probes, e.g. 'Spring Boot'")
    difficulty: str = Field(description="one of: easy, medium, hard")
    expected_points: list[str] = Field(
        description="Key points a strong answer should hit; used by the evaluator"
    )
    rationale: str = Field(description="Why this question fits the candidate — not shown to them")


class AnswerEvaluation(BaseModel):
    """Feature 9 — per-answer scoring. Scores are 0-100."""

    technical_score: int = Field(ge=0, le=100)
    communication: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    grammar: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)
    feedback: str = Field(description="Two sentences max, addressed to the candidate")
    covered_points: list[str]
    missed_points: list[str]
    red_flags: list[str] = Field(description="Factual errors or misconceptions stated")


class InterviewerDecision(BaseModel):
    """Feature 6 — what a human interviewer would do next.

    `action` drives the engine:
      follow_up -> probe deeper on the same topic
      hint      -> candidate stalled; nudge, keep the same topic open
      next      -> topic is done, move to a fresh question
      end       -> enough signal gathered, wrap up
    """

    action: str = Field(description="one of: follow_up, hint, next, end")
    reason: str = Field(description="One line of interviewer reasoning — internal only")
    message: str = Field(
        description=(
            "The exact text to say to the candidate for follow_up/hint. "
            "Empty string when action is next or end."
        )
    )
    skill_tag: str = Field(description="Topic in play; empty string if not applicable")
