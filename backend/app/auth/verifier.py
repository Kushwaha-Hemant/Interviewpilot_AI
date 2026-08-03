"""Token verification behind a swappable interface.

`AUTH_PROVIDER=local` issues and verifies our own JWTs (works with zero external setup).
`AUTH_PROVIDER=clerk` verifies Clerk-issued JWTs against Clerk's JWKS instead — the rest
of the app is unchanged because both return the same `AuthIdentity`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import settings
from app.core.security import TokenError, decode_access_token


@dataclass(frozen=True)
class AuthIdentity:
    """Who the bearer token says the caller is, provider-independent."""

    subject: str  # our user id (local) or Clerk user id
    email: str | None = None
    full_name: str | None = None
    is_external: bool = False


class TokenVerifier(ABC):
    @abstractmethod
    def verify(self, token: str) -> AuthIdentity: ...


class LocalJWTVerifier(TokenVerifier):
    def verify(self, token: str) -> AuthIdentity:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise TokenError("Token is missing a subject claim")
        return AuthIdentity(
            subject=subject,
            email=payload.get("email"),
            full_name=payload.get("name"),
            is_external=False,
        )


class ClerkVerifier(TokenVerifier):
    """Verifies Clerk session JWTs via Clerk's JWKS endpoint.

    Set CLERK_JWKS_URL (https://<your-instance>.clerk.accounts.dev/.well-known/jwks.json)
    and CLERK_ISSUER, then AUTH_PROVIDER=clerk. Users are provisioned on first request
    (see `resolve_user` in app/auth/dependencies.py).
    """

    def __init__(self) -> None:
        if not settings.clerk_jwks_url or not settings.clerk_issuer:
            raise TokenError(
                "AUTH_PROVIDER=clerk requires CLERK_JWKS_URL and CLERK_ISSUER to be set"
            )
        import jwt  # local import: only needed on this path

        self._jwt = jwt
        self._jwks = jwt.PyJWKClient(settings.clerk_jwks_url, cache_keys=True)

    def verify(self, token: str) -> AuthIdentity:
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            payload = self._jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=settings.clerk_issuer,
                options={"verify_aud": False},
            )
        except Exception as exc:  # PyJWKClient raises several unrelated types
            raise TokenError(f"Clerk token verification failed: {exc}") from exc

        subject = payload.get("sub")
        if not subject:
            raise TokenError("Clerk token is missing a subject claim")
        return AuthIdentity(
            subject=subject,
            email=payload.get("email") or payload.get("primary_email_address"),
            full_name=payload.get("name"),
            is_external=True,
        )


@lru_cache
def get_verifier() -> TokenVerifier:
    if settings.auth_provider == "clerk":
        return ClerkVerifier()
    return LocalJWTVerifier()
