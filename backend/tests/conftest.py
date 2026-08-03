"""Test bootstrap.

Environment is set BEFORE importing the app, because the engine and Settings are built
at import time. Tests run on SQLite + the mock AI provider, so they need no Docker and
no API key.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TEST_DB = BACKEND_DIR / "test.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["AI_PROVIDER"] = "mock"
os.environ["AUTH_PROVIDER"] = "local"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["STORAGE_DIR"] = str(BACKEND_DIR / "test-storage")
# Most tests exercise the interview product, not sign-up, so verification is off by
# default. test_email_verification.py flips it back on for its own cases.
os.environ["REQUIRE_EMAIL_VERIFICATION"] = "false"
os.environ["EMAIL_PROVIDER"] = "console"
# Cooldown must stay non-zero so the rate-limit test has something to assert against.
os.environ["OTP_RESEND_COOLDOWN_SECONDS"] = "60"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: E402,F401,F403


@pytest.fixture(scope="session", autouse=True)
def _database():
    if TEST_DB.exists():
        TEST_DB.unlink()
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A client already registered and carrying a bearer token."""
    import uuid

    email = f"candidate-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "correct-horse-battery", "full_name": "Test Candidate"},
    )
    assert response.status_code == 201, response.text
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


@pytest.fixture
def resume_pdf() -> bytes:
    """A small but realistic text-based resume PDF."""
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    lines = [
        "Alex Candidate",
        "Backend Engineer",
        "",
        "SKILLS",
        "Java, Spring Boot, React, PostgreSQL, Docker, AWS",
        "",
        "EXPERIENCE",
        "Acme Technologies - Software Engineer (2023 - Present)",
        "Built three production microservices in Java and Spring Boot.",
        "Reduced p95 latency from 800ms to 180ms by adding a Redis cache layer.",
        "",
        "PROJECTS",
        "Order Management Service - Spring Boot, PostgreSQL, Docker.",
        "Handled the full order lifecycle with asynchronous fulfilment.",
        "",
        "EDUCATION",
        "B.Tech Computer Science, 2023, 8.2 CGPA",
    ]
    y = 800
    for line in lines:
        pdf.drawString(60, y, line)
        y -= 18
    pdf.save()
    return buffer.getvalue()
