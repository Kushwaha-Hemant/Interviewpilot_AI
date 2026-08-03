"""Hit a RUNNING server end-to-end over real HTTP + WebSocket.

Unlike the pytest suite (in-process, SQLite), this exercises the deployed stack:
uvicorn, Postgres, CORS, and the live WebSocket. Run it with the server up:

    python scripts/smoke_live.py [http://127.0.0.1:8000]
"""

from __future__ import annotations

import json
import sys
import uuid
from urllib.parse import urlparse

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")


def ok(label: str, detail: str = "") -> None:
    print(f"  [ok] {label}{f' — {detail}' if detail else ''}")


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=60.0) as client:
        health = client.get("/health").json()
        assert health["status"] == "ok", health
        ok("health", f"ai={health['ai_provider']} auth={health['auth_provider']}")

        email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
        registered = client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery", "full_name": "Smoke Test"},
        )
        assert registered.status_code == 201, registered.text
        token = registered.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        ok("register + login", email)

        job = client.post(
            "/api/jobs",
            json={
                "raw_text": (
                    "Backend Engineer. We need 2+ years with Java, Spring Boot, PostgreSQL "
                    "and Docker. You will own REST APIs and deploy on AWS. Kubernetes a plus."
                )
            },
        )
        assert job.status_code == 201, job.text
        job_id = job.json()["id"]
        ok("job description parsed", f"{len(job.json()['parsed']['required_skills'])} skills")

        created = client.post(
            "/api/interviews",
            json={
                "mode": "technical",
                "role": "Backend Engineer",
                "company": "google",
                "planned_questions": 3,
                "job_id": job_id,
            },
        )
        assert created.status_code == 201, created.text
        interview_id = created.json()["id"]
        ok("interview created", created.json()["turns"][0]["question"][:60] + "…")

        answer = (
            "Dependency injection hands a class its collaborators instead of letting it "
            "build them. I prefer constructor injection because required dependencies are "
            "explicit and the fields can be final, which makes unit testing trivial. The "
            "trade-off is that a long constructor signals the class is doing too much."
        )
        actions = []
        for _ in range(30):
            current = client.get(f"/api/interviews/{interview_id}/current-turn").json()
            if current is None:
                break
            result = client.post(
                f"/api/interviews/{interview_id}/answer", json={"answer": answer}
            ).json()
            actions.append(result["action"])
            if result["interview_status"] == "completed":
                break
        ok("interview loop", f"{len(actions)} turns, actions={actions}")

        report = client.post(f"/api/interviews/{interview_id}/report")
        assert report.status_code == 200, report.text
        ok("report", f"readiness={report.json()['readiness_percent']}%")

        pdf = client.get(f"/api/interviews/{interview_id}/report.pdf")
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF"), pdf.status_code
        ok("pdf export", f"{len(pdf.content)} bytes")

        dashboard = client.get("/api/dashboard").json()
        ok(
            "dashboard",
            f"avg={dashboard['average_score']} streak={dashboard['practice_streak_days']}d",
        )

    # ---- WebSocket round trip
    from websockets.sync.client import connect

    host = urlparse(BASE).netloc
    ws_created_id = _new_interview(token, host)
    with connect(f"ws://{host}/ws/interview/{ws_created_id}?token={token}") as ws:
        frames = []
        while True:
            frame = json.loads(ws.recv())
            frames.append(frame["type"])
            if frame["type"] == "turn":
                break
        ws.send(json.dumps({"type": "answer", "text": "A reasonable answer about caching."}))
        while True:
            frame = json.loads(ws.recv())
            frames.append(frame["type"])
            if frame["type"] == "evaluation":
                score = frame["evaluation"]["overall"]
                break
        ok("websocket", f"frames={frames[:6]}… score={score}")

    print("\nAll live checks passed.")
    return 0


def _new_interview(token: str, host: str) -> str:
    with httpx.Client(base_url=f"http://{host}", timeout=60.0) as client:
        client.headers["Authorization"] = f"Bearer {token}"
        response = client.post("/api/interviews", json={"mode": "hr", "planned_questions": 2})
        response.raise_for_status()
        return response.json()["id"]


if __name__ == "__main__":
    raise SystemExit(main())
