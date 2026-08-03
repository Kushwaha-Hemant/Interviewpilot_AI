"""One-time verification codes.

A six digit code is only ~20 bits of entropy, so the secret alone is not what makes this
safe. The controls are:

  * codes are stored as a keyed HMAC, never in plaintext (key lives outside the DB)
  * a code expires after OTP_TTL_MINUTES
  * a code dies after OTP_MAX_ATTEMPTS wrong guesses — this is the real brute-force bound
  * issuing a new code invalidates every outstanding one for that user
  * sends are rate limited per user, with a cooldown between them
  * comparison is constant time
"""

from __future__ import annotations

import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.email import EmailError, get_email_sender
from app.email.templates import verification_email
from app.models.user import User
from app.models.verification import EmailVerification

logger = logging.getLogger(__name__)

PURPOSE_EMAIL_VERIFY = "email_verify"


class OTPError(Exception):
    """Base class for verification failures that are safe to show a user."""


class RateLimited(OTPError):
    def __init__(self, retry_after_seconds: int, message: str) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class InvalidCode(OTPError):
    pass


class AlreadyVerified(OTPError):
    """The address is already confirmed, so no code can buy a session here."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """SQLite hands back naive datetimes; Postgres hands back aware ones."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def hash_code(code: str) -> str:
    """Keyed digest. The pepper is SECRET_KEY, which is not stored in the database."""
    return hmac.new(settings.secret_key.encode(), code.encode(), sha256).hexdigest()


def generate_code() -> str:
    """A cryptographically random 6-digit code, leading zeros preserved."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _active_codes(db: Session, user_id: str) -> list[EmailVerification]:
    return list(
        db.scalars(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.purpose == PURPOSE_EMAIL_VERIFY,
                EmailVerification.consumed_at.is_(None),
            )
            .order_by(EmailVerification.created_at.desc())
        )
    )


def _recent_sends(db: Session, user_id: str) -> list[EmailVerification]:
    window_start = _now() - timedelta(hours=1)
    return [
        record
        for record in db.scalars(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.purpose == PURPOSE_EMAIL_VERIFY,
            )
            .order_by(EmailVerification.created_at.desc())
        )
        if _as_utc(record.created_at) >= window_start
    ]


def issue_code(db: Session, user: User, *, enforce_cooldown: bool = True) -> EmailVerification:
    """Create and email a fresh code, invalidating any outstanding ones.

    Raises RateLimited if the user is asking too often.
    """
    recent = _recent_sends(db, user.id)

    if enforce_cooldown and recent:
        since_last = (_now() - _as_utc(recent[0].created_at)).total_seconds()
        if since_last < settings.otp_resend_cooldown_seconds:
            wait = int(settings.otp_resend_cooldown_seconds - since_last)
            raise RateLimited(wait, f"Please wait {wait}s before requesting another code.")

    if len(recent) >= settings.otp_max_sends_per_hour:
        raise RateLimited(
            3600,
            "Too many codes requested. Please try again in an hour.",
        )

    # One live code at a time: an old code must not keep working after a resend.
    now = _now()
    for outstanding in _active_codes(db, user.id):
        outstanding.consumed_at = now

    code = generate_code()
    record = EmailVerification(
        user_id=user.id,
        code_hash=hash_code(code),
        purpose=PURPOSE_EMAIL_VERIFY,
        expires_at=now + timedelta(minutes=settings.otp_ttl_minutes),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    subject, html, text = verification_email(
        code=code, name=user.full_name, minutes=settings.otp_ttl_minutes
    )
    try:
        get_email_sender().send(to=user.email, subject=subject, html=html, text=text)
    except EmailError:
        # The code is already persisted; surface the delivery failure but keep the record
        # so a resend (which the user can trigger) reuses the same rate-limit window.
        logger.exception("Verification email delivery failed for %s", user.email)
        raise

    return record


def verify_code(db: Session, user: User, code: str) -> None:
    """Consume a code, or raise. Marks the user verified on success.

    An already-verified account MUST raise rather than short-circuit to success: the
    caller issues a session token on return, so treating "already verified" as a pass
    would let anyone mint a token for any confirmed address by posting a junk code.
    Verified users authenticate with their password, not with this endpoint.
    """
    if user.is_verified:
        raise AlreadyVerified("This email is already verified — please sign in.")

    submitted = (code or "").strip()
    if not submitted.isdigit() or len(submitted) != 6:
        raise InvalidCode("Enter the 6-digit code from your email.")

    now = _now()
    candidates = _active_codes(db, user.id)
    if not candidates:
        raise InvalidCode("That code has expired. Request a new one.")

    record = candidates[0]

    if _as_utc(record.expires_at) < now:
        record.consumed_at = now
        db.commit()
        raise InvalidCode("That code has expired. Request a new one.")

    if record.attempts >= settings.otp_max_attempts:
        record.consumed_at = now
        db.commit()
        raise InvalidCode("Too many incorrect attempts. Request a new code.")

    if not hmac.compare_digest(record.code_hash, hash_code(submitted)):
        record.attempts += 1
        remaining = settings.otp_max_attempts - record.attempts
        if remaining <= 0:
            record.consumed_at = now
            db.commit()
            raise InvalidCode("Too many incorrect attempts. Request a new code.")
        db.commit()
        raise InvalidCode(
            f"That code isn't right. {remaining} attempt{'s' if remaining != 1 else ''} left."
        )

    record.consumed_at = now
    user.is_verified = True
    user.verified_at = now
    db.commit()
    db.refresh(user)
