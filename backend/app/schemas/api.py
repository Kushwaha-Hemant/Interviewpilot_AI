"""Request/response models for the REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Difficulty, InterviewMode, InterviewStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------ auth


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: str
    email: str
    full_name: str | None
    is_recruiter: bool
    is_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class VerificationRequired(BaseModel):
    """Returned by register (and by login for an unverified account).

    Deliberately carries no access token — the account exists but cannot be used until
    the emailed code is confirmed.
    """

    status: str = "verification_required"
    email: EmailStr
    expires_in_minutes: int
    # True only when the backend is logging codes instead of emailing them, so the UI
    # can tell the developer where to look. Never true with a real SMTP host.
    delivery: str = "email"


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=10)


class ResendCodeRequest(BaseModel):
    email: EmailStr


# ---------------------------------------------------------------------------- resume


class ResumeOut(ORMModel):
    id: str
    filename: str
    parse_status: str
    parsed: dict[str, Any] | None
    parse_error: str | None
    created_at: datetime


# ------------------------------------------------------------------------------- job


class JobCreate(BaseModel):
    raw_text: str = Field(min_length=40, description="Pasted job description")
    title: str | None = None
    company: str | None = None


class JobOut(ORMModel):
    id: str
    title: str | None
    company: str | None
    parse_status: str
    parsed: dict[str, Any] | None
    parse_error: str | None
    created_at: datetime


# ------------------------------------------------------------------------- interview


class InterviewCreate(BaseModel):
    mode: InterviewMode = InterviewMode.TECHNICAL
    role: str = Field(default="Software Engineer", max_length=255)
    company: str = Field(default="generic", max_length=64)
    difficulty: Difficulty = Difficulty.MEDIUM
    planned_questions: int = Field(default=6, ge=1, le=20)
    resume_id: str | None = None
    job_id: str | None = None


class TurnOut(ORMModel):
    id: str
    sequence: int
    kind: str
    question: str
    skill_tag: str | None
    answer: str | None
    evaluation: dict[str, Any] | None
    overall_score: float | None
    created_at: datetime


class InterviewOut(ORMModel):
    id: str
    mode: str
    role: str
    company: str
    difficulty: str
    status: str
    planned_questions: int
    questions_asked: int
    focus_skills: list[str] | None
    overall_score: float | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class InterviewDetail(InterviewOut):
    turns: list[TurnOut] = []


class AnswerRequest(BaseModel):
    """REST fallback for clients not using the WebSocket."""

    answer: str = Field(default="", max_length=20000)
    duration_seconds: float | None = None


class TurnResult(BaseModel):
    evaluation: dict[str, Any]
    action: str
    message: str
    next_turn: TurnOut | None
    interview_status: InterviewStatus


# ---------------------------------------------------------------------------- report


class ReportOut(ORMModel):
    id: str
    interview_id: str
    summary: str
    technical_score: float | None
    communication_score: float | None
    confidence_score: float | None
    grammar_score: float | None
    clarity_score: float | None
    overall_score: float | None
    strengths: list[str] | None
    weaknesses: list[str] | None
    mistakes: list[dict[str, Any]] | None
    recommendations: list[dict[str, Any]] | None
    learning_plan: list[dict[str, Any]] | None
    skill_breakdown: list[dict[str, Any]] | None
    readiness_percent: float | None
    readiness_role: str | None
    estimated_prep_time: str | None
    created_at: datetime


# ------------------------------------------------------------------------- dashboard


class SkillStat(BaseModel):
    skill: str
    score: float
    attempts: int


class TimelinePoint(BaseModel):
    date: datetime
    score: float
    mode: str
    interview_id: str


class DashboardOut(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: float | None
    practice_streak_days: int
    strong_skills: list[SkillStat]
    weak_skills: list[SkillStat]
    timeline: list[TimelinePoint]
    confidence_trend: list[TimelinePoint]
    ai_recommendation: str | None
    focus_skill: str | None


# ------------------------------------------------------------------------- recruiter


class InviteCreate(BaseModel):
    candidate_name: str | None = None
    candidate_email: EmailStr | None = None
    config: InterviewCreate = Field(default_factory=InterviewCreate)
    max_uses: int = Field(default=1, ge=1, le=100)


class InviteOut(ORMModel):
    id: str
    token: str
    candidate_name: str | None
    candidate_email: str | None
    config: dict[str, Any]
    max_uses: int
    uses: int
    interview_id: str | None
    created_at: datetime
