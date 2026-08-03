"""FastAPI dependencies for authenticated routes and WebSockets."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.verifier import AuthIdentity, get_verifier
from app.core.config import settings
from app.core.security import TokenError
from app.database.session import SessionLocal, get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def resolve_user(db: Session, identity: AuthIdentity) -> User:
    """Map a verified identity onto a User row, provisioning external users on first sight."""
    if identity.is_external:
        user = db.scalar(select(User).where(User.external_auth_id == identity.subject))
        if user is None and identity.email:
            user = db.scalar(select(User).where(User.email == identity.email))
            if user is not None:
                user.external_auth_id = identity.subject
        if user is None:
            user = User(
                email=identity.email or f"{identity.subject}@external.local",
                full_name=identity.full_name,
                external_auth_id=identity.subject,
                # The identity provider already proved this address.
                is_verified=True,
            )
            db.add(user)
        db.commit()
        db.refresh(user)
        return user

    user = db.get(User, identity.subject)
    if user is None:
        raise CREDENTIALS_EXC
    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise CREDENTIALS_EXC
    try:
        identity = get_verifier().verify(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = resolve_user(db, identity)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Tokens are only ever issued after verification, but check on every request too:
    # an account can be un-verified administratively, and a token outlives that change.
    if settings.require_email_verification and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="email_not_verified"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


async def authenticate_websocket(token: str | None) -> tuple[User, Session] | None:
    """Authenticate a WebSocket from its `?token=` query param.

    Browsers cannot set headers on a WebSocket handshake, so the token rides in the query
    string. Returns (user, session); the CALLER owns closing the session.
    """
    if not token:
        return None
    try:
        identity = get_verifier().verify(token)
    except TokenError:
        return None

    db = SessionLocal()
    try:
        user = resolve_user(db, identity)
    except HTTPException:
        db.close()
        return None
    if not user.is_active or (settings.require_email_verification and not user.is_verified):
        db.close()
        return None
    return user, db


WebSocketToken = Annotated[str | None, Query(alias="token")]
