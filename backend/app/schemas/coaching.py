"""Structured Output schemas for the report + career-coach stages (features 10, 12, 14)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Mistake(BaseModel):
    topic: str
    what_went_wrong: str
    correct_answer: str


class Recommendation(BaseModel):
    topic: str
    why: str
    resources: list[str] = Field(description="Concrete docs, courses or books")


class LearningStep(BaseModel):
    week: int
    focus: str
    tasks: list[str]
    mini_project: str = Field(description="A small buildable project, or empty string")


class SkillScore(BaseModel):
    skill: str
    score: int = Field(ge=0, le=100)


class CoachReport(BaseModel):
    """Features 10 + 12 + 14 — the end-of-interview coaching payload."""

    summary: str = Field(description="3-5 sentence recruiter-readable summary")
    strengths: list[str]
    weaknesses: list[str]
    mistakes: list[Mistake]
    recommendations: list[Recommendation]
    learning_plan: list[LearningStep]
    skill_breakdown: list[SkillScore]
    readiness_percent: int = Field(ge=0, le=100)
    readiness_role: str = Field(description="Role the percentage refers to")
    estimated_prep_time: str = Field(description="e.g. '3 weeks'")


class DashboardInsight(BaseModel):
    """Feature 2 — the single AI recommendation shown on the dashboard."""

    recommendation: str = Field(description="One actionable sentence")
    focus_skill: str
    reason: str
