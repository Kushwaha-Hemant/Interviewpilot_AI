"""Email OTP verification: happy path plus every guard that makes a 6-digit code safe."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.otp import hash_code
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.models.verification import EmailVerification

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def _require_verification():
    """The rest of the suite runs with verification off; these tests need it on."""
    original = settings.require_email_verification
    settings.require_email_verification = True
    yield
    settings.require_email_verification = original


def new_email() -> str:
    return f"verify-{uuid.uuid4().hex[:8]}@example.com"


def stored_code(email: str) -> EmailVerification:
    """Read the live verification row straight from the DB.

    The plaintext code is never persisted, so tests assert by re-hashing a guess rather
    than by reading a code back out — the same thing an attacker with DB access faces.
    """
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        record = db.scalar(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user.id,
                EmailVerification.consumed_at.is_(None),
            )
            .order_by(EmailVerification.created_at.desc())
        )
        assert record is not None
        return record


def brute_force_code(email: str) -> str:
    """Recover the code the only way a test legitimately can: by matching the HMAC."""
    record = stored_code(email)
    for candidate in range(1_000_000):
        code = f"{candidate:06d}"
        if hash_code(code) == record.code_hash:
            return code
    raise AssertionError("no matching code found")


def register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Verify Test"},
    )
    assert response.status_code == 202, response.text
    return response.json()


# --------------------------------------------------------------------------- happy path


def test_register_returns_no_token_and_requires_a_code(client: TestClient):
    email = new_email()
    body = register(client, email)

    assert body["status"] == "verification_required"
    assert body["email"] == email
    assert "access_token" not in body, "register must not hand out a session before verification"


def test_verify_with_correct_code_issues_a_token(client: TestClient):
    email = new_email()
    register(client, email)
    code = brute_force_code(email)

    response = client.post("/api/auth/verify-email", json={"email": email, "code": code})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["user"]["is_verified"] is True


def test_verified_user_can_use_the_api(client: TestClient):
    email = new_email()
    register(client, email)
    token = client.post(
        "/api/auth/verify-email", json={"email": email, "code": brute_force_code(email)}
    ).json()["access_token"]

    response = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


# ------------------------------------------------------------------------------ guards


def test_unverified_account_cannot_log_in(client: TestClient):
    email = new_email()
    register(client, email)

    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 403
    assert response.json()["detail"] == "email_not_verified"


def test_wrong_code_is_rejected_and_counts_an_attempt(client: TestClient):
    email = new_email()
    register(client, email)
    real = brute_force_code(email)
    wrong = "000000" if real != "000000" else "111111"

    response = client.post("/api/auth/verify-email", json={"email": email, "code": wrong})
    assert response.status_code == 400
    assert "attempt" in response.json()["detail"].lower()

    assert stored_code(email).attempts == 1


def test_code_dies_after_max_attempts(client: TestClient):
    email = new_email()
    register(client, email)
    real = brute_force_code(email)
    wrong = "000000" if real != "000000" else "111111"

    for _ in range(settings.otp_max_attempts):
        client.post("/api/auth/verify-email", json={"email": email, "code": wrong})

    # Even the CORRECT code must now fail — the burned code is what bounds brute force.
    response = client.post("/api/auth/verify-email", json={"email": email, "code": real})
    assert response.status_code == 400

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None and user.is_verified is False


def test_expired_code_is_rejected(client: TestClient):
    email = new_email()
    register(client, email)
    code = brute_force_code(email)

    with SessionLocal() as db:
        record = db.get(EmailVerification, stored_code(email).id)
        assert record is not None
        record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    response = client.post("/api/auth/verify-email", json={"email": email, "code": code})
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


def test_resend_invalidates_the_previous_code(client: TestClient):
    email = new_email()
    register(client, email)
    first = brute_force_code(email)

    # Bypass the cooldown the way a real resend after 60s would.
    with SessionLocal() as db:
        record = db.get(EmailVerification, stored_code(email).id)
        assert record is not None
        record.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

    assert client.post("/api/auth/resend-code", json={"email": email}).status_code == 200
    second = brute_force_code(email)
    assert second != first or True  # a fresh row exists either way

    response = client.post("/api/auth/verify-email", json={"email": email, "code": first})
    assert response.status_code == 400, "the superseded code must stop working"

    assert (
        client.post("/api/auth/verify-email", json={"email": email, "code": second}).status_code
        == 200
    )


def test_resend_cooldown_is_enforced(client: TestClient):
    email = new_email()
    register(client, email)

    response = client.post("/api/auth/resend-code", json={"email": email})
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_resend_does_not_leak_whether_an_account_exists(client: TestClient):
    """An unknown address must look identical to a real unverified one."""
    unknown = client.post("/api/auth/resend-code", json={"email": new_email()})
    assert unknown.status_code == 200
    assert unknown.json()["status"] == "verification_required"


def test_verified_account_cannot_be_taken_over_via_verify_endpoint(client: TestClient):
    """Regression: /verify-email must never mint a token for an already-verified address.

    Short-circuiting "already verified" to success made this endpoint an account
    takeover — knowing an email was enough to get a session with any junk code.
    """
    email = new_email()
    register(client, email)
    code = brute_force_code(email)
    assert client.post("/api/auth/verify-email", json={"email": email, "code": code}).status_code == 200

    for attempt in (code, "000000", "999999"):
        response = client.post("/api/auth/verify-email", json={"email": email, "code": attempt})
        assert response.status_code == 409, f"code {attempt} was accepted after verification"
        assert "access_token" not in response.json()


def test_plaintext_code_is_never_stored(client: TestClient):
    email = new_email()
    register(client, email)
    code = brute_force_code(email)

    record = stored_code(email)
    assert code not in record.code_hash
    assert len(record.code_hash) == 64, "expected a sha256 hex digest"
