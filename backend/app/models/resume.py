from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, new_uuid
from app.database.types import JSONType

if TYPE_CHECKING:
    from app.models.user import User


class Resume(Base, TimestampMixin):
    """An uploaded resume plus the structured profile GPT extracted from it."""

    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Structured extraction — see app/schemas/extraction.ResumeProfile
    parsed: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    parse_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="resumes")

    @property
    def skills(self) -> list[str]:
        if not self.parsed:
            return []
        return [s.get("name", "") for s in self.parsed.get("skills", []) if s.get("name")]
