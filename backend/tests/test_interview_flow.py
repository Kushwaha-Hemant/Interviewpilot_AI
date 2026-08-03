"""End-to-end: resume -> JD -> adaptive interview -> report -> PDF -> dashboard."""

from __future__ import annotations

from fastapi.testclient import TestClient

JOB_DESCRIPTION = """
Backend Engineer - Payments

We are looking for a backend engineer with 2+ years of experience building services in
Java and Spring Boot. You will design REST APIs, own PostgreSQL schemas, and deploy with
Docker on AWS. Experience with Kubernetes and microservices is a plus.

Responsibilities:
- Design and build backend services for the payments platform
- Own reliability, monitoring and on-call for your services
- Collaborate with product and frontend engineers
"""

GOOD_ANSWER = (
    "Dependency injection means an object receives its collaborators from outside rather "
    "than constructing them itself. In Spring Boot the container owns the lifecycle and "
    "wires beans in. I prefer constructor injection because it makes required "
    "dependencies explicit and lets the field be final, which also makes the class "
    "trivially testable without a Spring context. Field injection hides dependencies and "
    "makes it easy to build an object in an invalid state. The trade-off is that a "
    "constructor with many parameters is a smell telling you the class does too much."
)


def test_health(client: TestClient):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["ai_provider"] == "mock"


def test_auth_rejects_bad_password(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "correct-horse-battery"},
    )
    response = client.post(
        "/api/auth/login", json={"email": "dup@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient):
    assert client.get("/api/dashboard").status_code == 401


def test_full_interview_flow(auth_client: TestClient, resume_pdf: bytes):
    # --- feature 3: resume upload + structured extraction
    upload = auth_client.post(
        "/api/resumes",
        files={"file": ("alex.pdf", resume_pdf, "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    resume = upload.json()
    assert resume["parse_status"] == "ready"
    assert resume["parsed"]["skills"], "expected extracted skills"

    # --- feature 4: job description extraction
    job_response = auth_client.post("/api/jobs", json={"raw_text": JOB_DESCRIPTION})
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()
    assert job["parse_status"] == "ready"
    assert job["parsed"]["required_skills"]

    # --- feature 5: interview created with the opening question already generated
    created = auth_client.post(
        "/api/interviews",
        json={
            "mode": "technical",
            "role": "Backend Engineer",
            "company": "amazon",
            "difficulty": "medium",
            "planned_questions": 3,
            "resume_id": resume["id"],
            "job_id": job["id"],
        },
    )
    assert created.status_code == 201, created.text
    interview = created.json()
    assert interview["focus_skills"], "focus skills should be derived from resume + JD"
    assert len(interview["turns"]) == 1
    assert interview["turns"][0]["kind"] == "question"

    interview_id = interview["id"]

    # --- features 6 + 9: answer loop with evaluation, follow-ups and hints
    seen_actions = set()
    for _ in range(30):
        current = auth_client.get(f"/api/interviews/{interview_id}/current-turn").json()
        if current is None:
            break
        result = auth_client.post(
            f"/api/interviews/{interview_id}/answer",
            json={"answer": GOOD_ANSWER, "duration_seconds": 42.0},
        )
        assert result.status_code == 200, result.text
        payload = result.json()

        evaluation = payload["evaluation"]
        for dimension in ("technical_score", "communication", "confidence", "grammar", "clarity", "overall"):
            assert 0 <= evaluation[dimension] <= 100

        seen_actions.add(payload["action"])
        if payload["interview_status"] == "completed":
            break
    else:
        raise AssertionError("interview did not terminate within 30 turns")

    detail = auth_client.get(f"/api/interviews/{interview_id}").json()
    assert detail["status"] == "completed"
    assert detail["questions_asked"] == 3, "should stop at the planned question budget"
    assert seen_actions & {"follow_up", "hint", "next", "end"}
    assert all(t["evaluation"] for t in detail["turns"] if t["answer"] is not None)

    # --- features 10/12/14: report
    report = auth_client.post(f"/api/interviews/{interview_id}/report")
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["summary"]
    assert body["learning_plan"]
    assert body["skill_breakdown"]
    assert 0 <= body["readiness_percent"] <= 100
    assert body["overall_score"] is not None

    pdf = auth_client.get(f"/api/interviews/{interview_id}/report.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF"), "expected a real PDF payload"
    assert len(pdf.content) > 2000

    # --- features 2 + 11: dashboard analytics
    dashboard = auth_client.get("/api/dashboard").json()
    assert dashboard["total_interviews"] == 1
    assert dashboard["completed_interviews"] == 1
    assert dashboard["average_score"] is not None
    assert dashboard["practice_streak_days"] >= 1
    assert dashboard["timeline"]
    assert dashboard["ai_recommendation"]


def test_question_budget_is_enforced_server_side(auth_client: TestClient):
    """The model can ask for more follow-ups forever; the engine must still terminate."""
    created = auth_client.post(
        "/api/interviews", json={"mode": "hr", "role": "Product Engineer", "planned_questions": 2}
    )
    interview_id = created.json()["id"]

    turns = 0
    while turns < 40:
        current = auth_client.get(f"/api/interviews/{interview_id}/current-turn").json()
        if current is None:
            break
        auth_client.post(f"/api/interviews/{interview_id}/answer", json={"answer": "ok"})
        turns += 1

    detail = auth_client.get(f"/api/interviews/{interview_id}").json()
    assert detail["status"] == "completed"
    assert detail["questions_asked"] == 2

    # No more than 2 consecutive follow-ups anywhere in the transcript.
    streak = 0
    for turn in detail["turns"]:
        streak = streak + 1 if turn["kind"] == "follow_up" else 0
        assert streak <= 2, "engine allowed a third consecutive follow-up"


def test_websocket_interview_round_trip(auth_client: TestClient):
    created = auth_client.post(
        "/api/interviews", json={"mode": "technical", "planned_questions": 2}
    )
    interview_id = created.json()["id"]
    token = auth_client.headers["Authorization"].split()[1]

    with auth_client.websocket_connect(
        f"/ws/interview/{interview_id}?token={token}"
    ) as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connected"
        assert connected["turn"] is not None

        assert ws.receive_json()["type"] == "speaking"
        question = ""
        while True:
            frame = ws.receive_json()
            if frame["type"] == "delta":
                question += frame["text"]
            elif frame["type"] == "turn":
                assert frame["turn"]["question"].strip() == question.strip()
                break

        ws.send_json({"type": "answer", "text": GOOD_ANSWER, "duration_seconds": 30})
        assert ws.receive_json() == {"type": "thinking", "stage": "evaluating"}

        evaluation_frame = ws.receive_json()
        assert evaluation_frame["type"] == "evaluation"
        assert 0 <= evaluation_frame["evaluation"]["overall"] <= 100


def test_websocket_rejects_bad_token(client: TestClient, auth_client: TestClient):
    created = auth_client.post("/api/interviews", json={"mode": "hr"})
    interview_id = created.json()["id"]

    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interview/{interview_id}?token=garbage") as ws:
            ws.receive_json()


def test_user_cannot_read_another_users_interview(client: TestClient, auth_client: TestClient):
    created = auth_client.post("/api/interviews", json={"mode": "hr"})
    interview_id = created.json()["id"]

    other = TestClient(auth_client.app)
    registered = other.post(
        "/api/auth/register",
        json={"email": "intruder@example.com", "password": "correct-horse-battery"},
    )
    other.headers["Authorization"] = f"Bearer {registered.json()['access_token']}"
    assert other.get(f"/api/interviews/{interview_id}").status_code == 404
