"""Live interview transport.

Protocol (JSON frames)
----------------------
client -> server
  {"type": "answer", "text": "...", "duration_seconds": 12.4}
  {"type": "finish"}
  {"type": "ping"}

server -> client
  {"type": "connected",   "interview": {...}, "turn": {...} | null}
  {"type": "speaking",    "kind": "question" | "follow_up" | "hint"}
  {"type": "delta",       "text": "next chunk of the interviewer's line"}
  {"type": "turn",        "turn": {...}}        # authoritative, after the deltas
  {"type": "thinking",    "stage": "evaluating" | "deciding"}
  {"type": "evaluation",  "turn_id": "...", "evaluation": {...}}
  {"type": "completed",   "interview_id": "..."}
  {"type": "error",       "detail": "..."}
  {"type": "pong"}

Note on `delta`: questions come from a Structured Output call, which must complete before
it can be validated — so the deltas are the finished line relayed in chunks to drive the
typewriter effect in the UI. It is presentation, not model streaming, and is marked as
such deliberately.
"""

from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import authenticate_websocket
from app.interview.engine import InterviewEngine
from app.models.enums import InterviewStatus
from app.models.interview import Interview, InterviewTurn
from app.schemas.api import InterviewOut, TurnOut

logger = logging.getLogger(__name__)

router = APIRouter()

DELTA_DELAY_SECONDS = 0.018
CLOSE_POLICY_VIOLATION = 1008
CLOSE_NORMAL = 1000


def _turn_payload(turn: InterviewTurn | None) -> dict | None:
    return TurnOut.model_validate(turn).model_dump(mode="json") if turn else None


async def _emit_line(ws: WebSocket, turn: InterviewTurn) -> None:
    """Announce a new interviewer line: kind, deltas, then the authoritative turn."""
    await ws.send_json({"type": "speaking", "kind": turn.kind})
    for chunk in re.findall(r"\S+\s*", turn.question):
        await ws.send_json({"type": "delta", "text": chunk})
        await asyncio.sleep(DELTA_DELAY_SECONDS)
    await ws.send_json({"type": "turn", "turn": _turn_payload(turn)})


def _load_interview(db: Session, interview_id: str, user_id: str) -> Interview | None:
    interview = db.scalar(
        select(Interview)
        .options(selectinload(Interview.turns))
        .where(Interview.id == interview_id)
    )
    if interview is None or interview.user_id != user_id:
        return None
    return interview


@router.websocket("/ws/interview/{interview_id}")
async def interview_socket(websocket: WebSocket, interview_id: str, token: str | None = None) -> None:
    # Browsers can't set headers on a WS handshake, so the JWT rides in ?token=.
    authenticated = await authenticate_websocket(token)
    if authenticated is None:
        await websocket.close(code=CLOSE_POLICY_VIOLATION, reason="Unauthorized")
        return

    user, db = authenticated
    try:
        interview = _load_interview(db, interview_id, user.id)
        if interview is None:
            await websocket.close(code=CLOSE_POLICY_VIOLATION, reason="Interview not found")
            return

        await websocket.accept()
        engine = InterviewEngine(db)

        # Resume support: reconnecting mid-session re-sends the open question.
        if not interview.turns:
            await engine.start(interview)
        open_turn = engine.current_turn(interview)

        await websocket.send_json(
            {
                "type": "connected",
                "interview": InterviewOut.model_validate(interview).model_dump(mode="json"),
                "turn": _turn_payload(open_turn),
            }
        )
        if open_turn is not None:
            await _emit_line(websocket, open_turn)
        elif interview.status == InterviewStatus.COMPLETED:
            await websocket.send_json({"type": "completed", "interview_id": interview.id})

        await _run_loop(websocket, db, engine, interview)

    except WebSocketDisconnect:
        logger.info("Candidate disconnected from interview %s", interview_id)
    except Exception:
        logger.exception("Interview socket failed for %s", interview_id)
        try:
            await websocket.send_json({"type": "error", "detail": "Interview session failed"})
            await websocket.close(code=CLOSE_NORMAL)
        except Exception:
            pass
    finally:
        db.close()


async def _run_loop(
    websocket: WebSocket, db: Session, engine: InterviewEngine, interview: Interview
) -> None:
    while True:
        message = await websocket.receive_json()
        kind = message.get("type")

        if kind == "ping":
            await websocket.send_json({"type": "pong"})
            continue

        if kind == "finish":
            if interview.status != InterviewStatus.COMPLETED:
                engine.complete(interview)
            await websocket.send_json({"type": "completed", "interview_id": interview.id})
            await websocket.close(code=CLOSE_NORMAL)
            return

        if kind != "answer":
            await websocket.send_json({"type": "error", "detail": f"Unknown message type: {kind}"})
            continue

        if interview.status == InterviewStatus.COMPLETED:
            await websocket.send_json({"type": "error", "detail": "This interview is complete"})
            continue

        turn = engine.current_turn(interview)
        if turn is None:
            await websocket.send_json({"type": "error", "detail": "No open question"})
            continue

        await websocket.send_json({"type": "thinking", "stage": "evaluating"})
        outcome = await engine.submit_answer(
            interview,
            turn,
            str(message.get("text") or ""),
            duration_seconds=message.get("duration_seconds"),
        )

        await websocket.send_json(
            {
                "type": "evaluation",
                "turn_id": turn.id,
                "evaluation": outcome.evaluation.model_dump(),
            }
        )

        if outcome.next_turn is not None:
            await websocket.send_json({"type": "thinking", "stage": "deciding"})
            await _emit_line(websocket, outcome.next_turn)

        if outcome.finished:
            await websocket.send_json({"type": "completed", "interview_id": interview.id})
            await websocket.close(code=CLOSE_NORMAL)
            return
