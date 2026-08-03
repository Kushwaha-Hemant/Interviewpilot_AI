"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { API_BASE, getToken } from "@/services/api";
import type { ClientFrame, Evaluation, Interview, ServerFrame, Turn, TurnKind } from "@/types";

export interface TranscriptEntry {
  id: string;
  role: "interviewer" | "candidate";
  kind?: TurnKind;
  text: string;
  evaluation?: Evaluation;
}

export type SocketStatus = "connecting" | "open" | "closed" | "error";

interface State {
  status: SocketStatus;
  interview: Interview | null;
  currentTurn: Turn | null;
  transcript: TranscriptEntry[];
  /** The interviewer's line as it types out. */
  streaming: string;
  speakingKind: TurnKind | null;
  thinking: "evaluating" | "deciding" | null;
  completed: boolean;
  error: string | null;
}

const INITIAL: State = {
  status: "connecting",
  interview: null,
  currentTurn: null,
  transcript: [],
  streaming: "",
  speakingKind: null,
  thinking: null,
  completed: false,
  error: null,
};

function wsUrl(interviewId: string, token: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/ws/interview/${interviewId}?token=${encodeURIComponent(token)}`;
}

export function useInterviewSocket(interviewId: string) {
  const [state, setState] = useState<State>(INITIAL);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setState((s) => ({ ...s, status: "error", error: "You are not signed in." }));
      return;
    }

    // React StrictMode mounts effects twice in development. Do NOT guard with a ref —
    // the cleanup from the first run would close the only socket and the guard would
    // stop the second run from opening a replacement. Instead let each run own its
    // socket and dispose of it properly; the surviving mount keeps a live connection.
    const socket = new WebSocket(wsUrl(interviewId, token));
    socketRef.current = socket;
    let disposed = false;

    socket.onopen = () => {
      // Closing a socket that is still CONNECTING is a no-op in some browsers, so a
      // socket disposed mid-handshake is closed here instead.
      if (disposed) {
        socket.close();
        return;
      }
      setState((s) => ({ ...s, status: "open" }));
    };

    socket.onmessage = (event) => {
      if (disposed) return;
      const frame = JSON.parse(event.data as string) as ServerFrame;
      setState((s) => reduce(s, frame));
    };

    socket.onerror = () => {
      if (disposed) return;
      setState((s) => ({ ...s, status: "error", error: "Connection to the interviewer failed." }));
    };

    socket.onclose = () => {
      if (disposed) return;
      setState((s) => ({ ...s, status: s.completed ? "closed" : s.status }));
    };

    // Keeps idle proxies from dropping a long thinking pause.
    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "ping" }));
    }, 25_000);

    return () => {
      disposed = true;
      window.clearInterval(heartbeat);
      if (socket.readyState === WebSocket.OPEN) socket.close();
    };
  }, [interviewId]);

  const send = useCallback((frame: ClientFrame) => {
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(frame));
  }, []);

  const sendAnswer = useCallback(
    (text: string, durationSeconds?: number) => {
      setState((s) => ({
        ...s,
        currentTurn: null,
        transcript: [
          ...s.transcript,
          { id: `answer-${s.transcript.length}`, role: "candidate", text },
        ],
      }));
      send({ type: "answer", text, duration_seconds: durationSeconds });
    },
    [send],
  );

  const finish = useCallback(() => send({ type: "finish" }), [send]);

  return { ...state, sendAnswer, finish };
}

function reduce(state: State, frame: ServerFrame): State {
  switch (frame.type) {
    case "connected":
      return { ...state, interview: frame.interview, currentTurn: frame.turn };

    case "speaking":
      return { ...state, speakingKind: frame.kind, streaming: "", thinking: null };

    case "delta":
      return { ...state, streaming: state.streaming + frame.text };

    case "turn": {
      // The `turn` frame is authoritative — replace whatever the deltas built up.
      const alreadyLogged = state.transcript.some((e) => e.id === frame.turn.id);
      return {
        ...state,
        currentTurn: frame.turn,
        streaming: "",
        speakingKind: null,
        transcript: alreadyLogged
          ? state.transcript
          : [
              ...state.transcript,
              {
                id: frame.turn.id,
                role: "interviewer",
                kind: frame.turn.kind,
                text: frame.turn.question,
              },
            ],
      };
    }

    case "thinking":
      return { ...state, thinking: frame.stage };

    case "evaluation": {
      // Attach the score to the candidate answer that produced it (the last one).
      const transcript = [...state.transcript];
      for (let i = transcript.length - 1; i >= 0; i--) {
        if (transcript[i].role === "candidate" && !transcript[i].evaluation) {
          transcript[i] = { ...transcript[i], evaluation: frame.evaluation };
          break;
        }
      }
      return { ...state, transcript, thinking: null };
    }

    case "completed":
      return { ...state, completed: true, currentTurn: null, thinking: null, streaming: "" };

    case "error":
      return { ...state, error: frame.detail, thinking: null };

    default:
      return state;
  }
}
