from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, new_uuid
from app.database.types import JSONType

if TYPE_CHECKING:
    from app.models.user import User


class JobDescription(Base, TimestampMixin):
    """A pasted JD plus its structured extraction."""

    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured extraction — see app/schemas/extraction.JobProfile
    parsed: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    parse_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="jobs")
