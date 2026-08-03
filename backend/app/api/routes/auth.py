"""Feature 1 — email/password auth with OTP email verification.

Social login arrives via AUTH_PROVIDER=clerk, where the identity provider has already
proven the address, so those users skip this flow entirely.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.auth.dependencies import CurrentUser, DbSession
from app.auth.otp import AlreadyVerified, InvalidCode, RateLimited, issue_code, verify_code
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.email import EmailError
from app.models.user import User
from app.schemas.api import (
    LoginRequest,
    RegisterRequest,
    ResendCodeRequest,
    TokenResponse,
    UserOut,
    VerificationRequired,
    VerifyEmailRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# 403 + this code is the frontend's signal to route the user to the verify screen
# rather than showing a generic error.
UNVERIFIED_DETAIL = "email_not_verified"


def _issue_token(user: User) -> TokenResponse:
    token = create_access_token(
        user.id, extra_claims={"email": user.email, "name": user.full_name}
    )
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


def _pending(user: User) -> VerificationRequired:
    return VerificationRequired(
        email=user.email,
        expires_in_minutes=settings.otp_ttl_minutes,
        delivery="console" if settings.resolved_email_provider == "console" else "email",
    )


def _send_code_or_503(db, user: User, *, enforce_cooldown: bool = True) -> None:
    try:
        issue_code(db, user, enforce_cooldown=enforce_cooldown)
    except RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except EmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't send the verification email. Please try again shortly.",
        ) from exc


# --------------------------------------------------------------------------- register


@router.post(
    "/register",
    response_model=TokenResponse | VerificationRequired,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, response: Response, db: DbSession):
    if settings.auth_provider != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is handled by {settings.auth_provider}",
        )

    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))

    if existing is not None:
        # An unverified account is not yet "taken" by anyone who proved ownership, so
        # re-registering resends the code instead of leaking that the address exists.
        if not existing.is_verified and settings.require_email_verification:
            existing.full_name = payload.full_name or existing.full_name
            existing.hashed_password = hash_password(payload.password)
            db.commit()
            _send_code_or_503(db, existing)
            return _pending(existing)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account with that email exists"
        )

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_verified=not settings.require_email_verification,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if not settings.require_email_verification:
        return _issue_token(user)

    _send_code_or_503(db, user, enforce_cooldown=False)
    response.status_code = status.HTTP_202_ACCEPTED
    return _pending(user)


# ----------------------------------------------------------------------------- verify


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(payload: VerifyEmailRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        # Same message as a wrong code — don't confirm which addresses are registered.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That code isn't right. Request a new one.",
        )

    try:
        verify_code(db, user, payload.code)
    except AlreadyVerified as exc:
        # 409, and deliberately NO token: this endpoint must never be a way to obtain a
        # session for an address someone merely knows.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidCode as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _issue_token(user)


@router.post("/resend-code", response_model=VerificationRequired)
def resend_code(payload: ResendCodeRequest, db: DbSession) -> VerificationRequired:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))

    # Always answer as though the address existed and was unverified: anything else
    # turns this endpoint into an account-enumeration oracle.
    if user is None or user.is_verified:
        return VerificationRequired(
            email=payload.email,
            expires_in_minutes=settings.otp_ttl_minutes,
            delivery="console" if settings.resolved_email_provider == "console" else "email",
        )

    _send_code_or_503(db, user)
    return _pending(user)


# ------------------------------------------------------------------------------ login


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.hashed_password or not verify_password(
        payload.password, user.hashed_password
    ):
        # Same message either way — don't leak which emails are registered.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    if settings.require_email_verification and not user.is_verified:
        # Credentials were correct, so sending a fresh code here is not an enumeration
        # risk. Swallow rate limiting: the user still needs routing to the verify screen.
        try:
            issue_code(db, user)
        except (RateLimited, EmailError):
            logger.info("Verification resend skipped on login for %s", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=UNVERIFIED_DETAIL)

    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
