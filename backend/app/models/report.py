from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, new_uuid
from app.database.types import JSONType

if TYPE_CHECKING:
    from app.models.interview import Interview


class InterviewReport(Base, TimestampMixin):
    """Post-interview summary: scores, coaching, learning plan, readiness."""

    __tablename__ = "interview_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    interview_id: Mapped[str] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Averaged per-dimension scores across all answered turns.
    technical_score: Mapped[float | None] = mapped_column(Float)
    communication_score: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    grammar_score: Mapped[float | None] = mapped_column(Float)
    clarity_score: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float)

    strengths: Mapped[list[str] | None] = mapped_column(JSONType)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSONType)
    mistakes: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType)
    recommendations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType)
    learning_plan: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType)

    # Feature 14 — career readiness verdict.
    readiness_percent: Mapped[float | None] = mapped_column(Float)
    readiness_role: Mapped[str | None] = mapped_column(String(255))
    estimated_prep_time: Mapped[str | None] = mapped_column(String(64))

    # Per-skill radar data: [{"skill": "Spring Boot", "score": 72}, ...]
    skill_breakdown: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType)

    pdf_path: Mapped[str | None] = mapped_column(String(1024))

    interview: Mapped["Interview"] = relationship(back_populates="report")
