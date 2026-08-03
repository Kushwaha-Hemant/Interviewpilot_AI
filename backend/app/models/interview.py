from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, new_uuid
from app.database.types import JSONType
from app.models.enums import Difficulty, InterviewMode, InterviewStatus, TurnKind

if TYPE_CHECKING:
    from app.models.report import InterviewReport
    from app.models.user import User


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resume_id: Mapped[str | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="SET NULL"), index=True
    )

    mode: Mapped[str] = mapped_column(
        String(32), default=InterviewMode.TECHNICAL, nullable=False
    )
    role: Mapped[str] = mapped_column(String(255), default="Software Engineer", nullable=False)
    company: Mapped[str] = mapped_column(String(64), default="generic", nullable=False)
    difficulty: Mapped[str] = mapped_column(
        String(16), default=Difficulty.MEDIUM, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=InterviewStatus.CREATED, index=True, nullable=False
    )

    # How many primary questions to ask before wrapping up.
    planned_questions: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    # Distinct primary questions asked so far (follow-ups/hints don't count).
    questions_asked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Focus areas the engine drew from the resume/JD at creation time.
    focus_skills: Mapped[list[str] | None] = mapped_column(JSONType)
    # Snapshot of resume/JD context so the interview stays reproducible.
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONType)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    overall_score: Mapped[float | None] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="interviews")
    turns: Mapped[list["InterviewTurn"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewTurn.sequence",
    )
    report: Mapped["InterviewReport | None"] = relationship(
        back_populates="interview", cascade="all, delete-orphan", uselist=False
    )


class InterviewTurn(Base, TimestampMixin):
    """One question -> answer -> evaluation exchange.

    A turn is created the moment the question is emitted; `answer_text` and `evaluation`
    are filled in when the candidate responds. `kind` distinguishes a fresh question from
    a follow-up probe or a hint, which is what makes the loop feel human (feature 6).
    """

    __tablename__ = "interview_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    interview_id: Mapped[str] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), index=True, nullable=False
    )

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), default=TurnKind.QUESTION, nullable=False)
    parent_turn_id: Mapped[str | None] = mapped_column(
        ForeignKey("interview_turns.id", ondelete="CASCADE")
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_meta: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    expected_points: Mapped[list[str] | None] = mapped_column(JSONType)
    skill_tag: Mapped[str | None] = mapped_column(String(128), index=True)

    answer: Mapped[str | None] = mapped_column(Text)
    answer_duration_seconds: Mapped[float | None] = mapped_column(Float)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Full evaluator payload — see app/schemas/evaluation.AnswerEvaluation
    evaluation: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    # Denormalised for cheap analytics queries.
    overall_score: Mapped[float | None] = mapped_column(Float, index=True)

    interview: Mapped["Interview"] = relationship(back_populates="turns")
