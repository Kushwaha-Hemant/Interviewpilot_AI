from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User


class EmailVerification(Base, TimestampMixin):
    """A one-time code issued to prove ownership of an email address.

    The code itself is NEVER stored — only an HMAC of it (see app/auth/otp.py). A six
    digit code has ~20 bits of entropy, so a plaintext or fast-unsalted-hash column
    would be trivially reversible if the database leaked. The HMAC is keyed with
    SECRET_KEY, which lives outside the database.
    """

    __tablename__ = "email_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), default="email_verify", nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Wrong guesses against THIS code. Burned codes stop accepting attempts entirely,
    # which is what makes a 6-digit secret safe against online brute force.
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="verifications")
