from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, new_uuid
from app.database.types import JSONType


class InterviewInvite(Base, TimestampMixin):
    """Feature 15 — a recruiter-created, shareable interview link.

    The recruiter fixes the interview config here; the candidate opens `token`, an
    Interview row is spun up from this config, and the recruiter reads the report.
    """

    __tablename__ = "interview_invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    recruiter_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    candidate_email: Mapped[str | None] = mapped_column(String(255))
    candidate_name: Mapped[str | None] = mapped_column(String(255))

    # Interview config the candidate's session is created from.
    config: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)

    max_uses: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    interview_id: Mapped[str | None] = mapped_column(
        ForeignKey("interviews.id", ondelete="SET NULL")
    )
