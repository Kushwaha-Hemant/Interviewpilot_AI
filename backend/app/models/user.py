from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.interview import Interview
    from app.models.job import JobDescription
    from app.models.resume import Resume
    from app.models.verification import EmailVerification


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255))

    # Populated when AUTH_PROVIDER=clerk; lets the same row back either auth mode.
    external_auth_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_recruiter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Email ownership proof. Local sign-ups start unverified and must confirm an OTP;
    # Clerk-provisioned users arrive already verified by the identity provider.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    verifications: Mapped[list["EmailVerification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["JobDescription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
