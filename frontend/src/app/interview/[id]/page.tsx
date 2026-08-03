"use client";

import { CheckCircle2, Lightbulb, Mic, Send, Square } from "lucide-react";
import { useRouter } from "next/navigation";
import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { SessionRail } from "@/components/interview/SessionRail";
import {
  Badge,
  Button,
  Card,
  CardBody,
  ErrorMessage,
  Skeleton,
  Tooltip,
} from "@/components/ui/primitives";
import { useInterviewSocket, type TranscriptEntry } from "@/hooks/useInterviewSocket";
import { scoreText, scoreToken } from "@/lib/score";
import { cn, modeLabel } from "@/lib/utils";
import { api } from "@/services/api";

const MAX_ANSWER_CHARS = 20_000;

export default function InterviewRoomPage({ params }: { params: Promise<{ id: string }> }) {
  // Next 16: route params arrive as a promise; client components unwrap with use().
  const { id } = use(params);
  return (
    <AppShell bare>
      <InterviewRoom interviewId={id} />
    </AppShell>
  );
}

function InterviewRoom({ interviewId }: { interviewId: string }) {
  const router = useRouter();
  const {
    status,
    interview,
    currentTurn,
    transcript,
    streaming,
    speakingKind,
    thinking,
    completed,
    error,
    sendAnswer,
    finish,
  } = useInterviewSocket(interviewId);

  const [answer, setAnswer] = useState("");
  const [askedAt, setAskedAt] = useState<number | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const boxRef = useRef<HTMLTextAreaElement>(null);

  const elapsed = useElapsed(status === "open" && !completed);
  const { recording, toggleRecording, transcribing, voiceError } = useVoiceAnswer(
    useCallback((text: string) => setAnswer((prev) => (prev ? `${prev} ${text}` : text)), []),
  );

  // `interview` only arrives once, on the `connected` frame, so its counters go stale.
  // Derive live state from the transcript instead.
  const questionsAsked = Math.max(
    transcript.filter((e) => e.role === "interviewer" && e.kind === "question").length,
    1,
  );
  const evaluations = useMemo(
    () => transcript.map((e) => e.evaluation).filter((e) => e != null),
    [transcript],
  );
  const runningAverage = evaluations.length
    ? Math.round(evaluations.reduce((sum, e) => sum + e.overall, 0) / evaluations.length)
    : null;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [transcript, streaming, thinking, completed]);

  // Start the clock and focus the box when a fresh question lands.
  useEffect(() => {
    if (currentTurn) {
      setAskedAt(Date.now());
      boxRef.current?.focus();
    }
  }, [currentTurn]);

  function submit() {
    const text = answer.trim();
    if (!text || !currentTurn) return;
    sendAnswer(text, askedAt ? (Date.now() - askedAt) / 1000 : undefined);
    setAnswer("");
  }

  async function goToReport() {
    setGeneratingReport(true);
    try {
      await api.createReport(interviewId);
    } catch {
      // The report page retries generation itself, so navigate regardless.
    }
    router.push(`/report/${interviewId}`);
  }

  const busy = thinking !== null || speakingKind !== null;
  const answered = transcript.filter((e) => e.role === "candidate").length;
  const canSend = !!currentTurn && !busy && answer.trim().length > 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-3.25rem)] w-full max-w-6xl gap-4 px-6 py-5">
      {/* ============================================================ main */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* -------------------------------------------------------- header */}
        <div className="flex flex-wrap items-center gap-3 pb-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="truncate text-lg font-semibold tracking-tight">
                {interview?.role ?? "Interview"}
              </h1>
              {interview && <Badge tone="accent">{modeLabel(interview.mode)}</Badge>}
              {status === "open" && !completed && (
                <span className="flex items-center gap-1.5 text-xs text-good">
                  <span className="live-dot h-1.5 w-1.5 rounded-full bg-good" />
                  Live
                </span>
              )}
            </div>
            <p className="mt-0.5 text-xs text-ink-tertiary">
              {interview ? (
                <>
                  <span className="capitalize">{interview.company}</span> style ·{" "}
                  {interview.difficulty} · question{" "}
                  {Math.min(questionsAsked, interview.planned_questions)} of{" "}
                  {interview.planned_questions}
                </>
              ) : (
                "Connecting to your interviewer…"
              )}
            </p>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <span className="tabular text-xs text-ink-faint xl:hidden">{elapsed}</span>
            {!completed && (
              <Button variant="ghost" size="sm" onClick={finish}>
                End interview
              </Button>
            )}
          </div>
        </div>

        {/* ---------------------------------------------------- transcript */}
        <div
          ref={scrollRef}
          className="surface-edge min-h-0 flex-1 space-y-5 overflow-y-auto rounded-lg border border-line-subtle bg-surface-1/60 p-5 backdrop-blur-xl"
        >
          {status === "connecting" && <ConnectingSkeleton />}

          {transcript.map((entry) => (
            <TranscriptEntryView key={entry.id} entry={entry} />
          ))}

          {streaming && (
            <Bubble role="interviewer" kind={speakingKind ?? "question"}>
              {streaming}
              <span className="caret ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-accent-bright" />
            </Bubble>
          )}

          {thinking && <ThinkingIndicator stage={thinking} />}

          {completed && (
            <Card className="border-good/30 bg-good-dim">
              <CardBody className="flex flex-wrap items-center gap-4">
                <span className="flex h-9 w-9 items-center justify-center rounded-md bg-good/15">
                  <CheckCircle2 className="h-4.5 w-4.5 text-good" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium">Interview complete</p>
                  <p className="mt-0.5 text-sm text-ink-secondary">
                    {answered} answer{answered === 1 ? "" : "s"} recorded
                    {runningAverage != null && ` · averaging ${runningAverage}/100`}.
                  </p>
                </div>
                <Button onClick={goToReport} loading={generatingReport}>
                  {generatingReport ? "Writing your report…" : "See my report"}
                </Button>
              </CardBody>
            </Card>
          )}
        </div>

        {/* ------------------------------------------------------ composer */}
        {!completed && (
          <div className="pt-4">
            <ErrorMessage>{error ?? voiceError}</ErrorMessage>

            <div
              className={cn(
                "surface-edge mt-2 rounded-lg border bg-surface-1/80 p-2.5 backdrop-blur-xl transition-colors duration-200",
                currentTurn && !busy ? "border-line" : "border-line-subtle",
              )}
            >
              <textarea
                ref={boxRef}
                rows={3}
                value={answer}
                maxLength={MAX_ANSWER_CHARS}
                disabled={!currentTurn || busy}
                placeholder={
                  currentTurn
                    ? "Type your answer, or press the mic to speak…"
                    : "Wait for the next question…"
                }
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    submit();
                  }
                }}
                className="w-full resize-none bg-transparent px-2 py-1.5 text-sm leading-relaxed text-ink placeholder:text-ink-faint focus:outline-none disabled:opacity-50"
              />

              <div className="flex items-center gap-2 px-1 pt-1">
                <span className="text-[0.6875rem] text-ink-faint">
                  {recording ? (
                    <span className="flex items-center gap-1.5 text-bad">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-bad" />
                      Recording — press stop when you&apos;re done
                    </span>
                  ) : (
                    <>
                      <kbd className="rounded-[3px] border border-line px-1 py-px font-sans">
                        Ctrl
                      </kbd>{" "}
                      +{" "}
                      <kbd className="rounded-[3px] border border-line px-1 py-px font-sans">
                        Enter
                      </kbd>{" "}
                      to send
                    </>
                  )}
                </span>

                {answer.length > 0 && (
                  <span className="tabular text-[0.6875rem] text-ink-faint">
                    {answer.trim().split(/\s+/).length} words
                  </span>
                )}

                <div className="ml-auto flex items-center gap-1.5">
                  <Tooltip label={recording ? "Stop recording" : "Answer with your voice"}>
                    <Button
                      variant={recording ? "danger" : "ghost"}
                      size="icon-sm"
                      onClick={toggleRecording}
                      disabled={!currentTurn || busy || transcribing}
                      aria-label={recording ? "Stop recording" : "Record your answer"}
                    >
                      {transcribing ? (
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current/25 border-t-current" />
                      ) : recording ? (
                        <Square className="h-3.5 w-3.5" />
                      ) : (
                        <Mic className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </Tooltip>

                  <Button size="sm" onClick={submit} disabled={!canSend} aria-label="Send answer">
                    Send
                    <Send className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ============================================================ rail */}
      <SessionRail
        interview={interview}
        questionsAsked={questionsAsked}
        answered={answered}
        elapsed={elapsed}
        runningAverage={runningAverage}
        latest={evaluations.at(-1) ?? null}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ pieces */

function TranscriptEntryView({ entry }: { entry: TranscriptEntry }) {
  return (
    <div className="space-y-2.5">
      <Bubble role={entry.role} kind={entry.kind}>
        {entry.text}
      </Bubble>
      {entry.evaluation && <EvaluationCard evaluation={entry.evaluation} />}
    </div>
  );
}

function EvaluationCard({ evaluation }: { evaluation: NonNullable<TranscriptEntry["evaluation"]> }) {
  return (
    <div className="ml-auto max-w-[86%] overflow-hidden rounded-md border border-line-subtle bg-surface-2/60">
      {/* Score strip: the band colour does the work, the number confirms it. */}
      <div className="flex items-center gap-3 border-b border-line-subtle px-3.5 py-2">
        <span className={cn("tabular text-sm font-semibold", scoreText(evaluation.overall))}>
          {evaluation.overall}
          <span className="text-ink-faint">/100</span>
        </span>
        <div className="flex flex-1 gap-1">
          {(
            [
              ["T", evaluation.technical_score],
              ["C", evaluation.communication],
              ["Cf", evaluation.confidence],
              ["G", evaluation.grammar],
              ["Cl", evaluation.clarity],
            ] as const
          ).map(([key, value]) => (
            <Tooltip key={key} label={`${DIMENSION_NAMES[key]}: ${value}`}>
              <span className="flex-1">
                <span className="block h-1 rounded-full bg-surface-3">
                  <span
                    className="block h-full rounded-full"
                    style={{ width: `${value}%`, background: scoreToken(value) }}
                  />
                </span>
              </span>
            </Tooltip>
          ))}
        </div>
      </div>

      <div className="px-3.5 py-2.5">
        <p className="text-xs leading-relaxed text-ink-secondary">{evaluation.feedback}</p>

        {/* Cap the list: an over-eager rubric can return a dozen points, which turns the
            feedback into an unreadable wall the candidate skips entirely. */}
        {evaluation.missed_points.length > 0 && (
          <div className="mt-2.5 border-t border-line-subtle pt-2.5">
            <p className="text-[0.6875rem] font-medium text-warn">Missed</p>
            <ul className="mt-1 space-y-1">
              {evaluation.missed_points.slice(0, 3).map((point) => (
                <li key={point} className="flex gap-1.5 text-[0.6875rem] leading-relaxed text-ink-tertiary">
                  <span className="text-warn">·</span>
                  {point}
                </li>
              ))}
            </ul>
            {evaluation.missed_points.length > 3 && (
              <p className="mt-1 text-[0.6875rem] text-ink-faint">
                +{evaluation.missed_points.length - 3} more in the full report
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const DIMENSION_NAMES = {
  T: "Technical",
  C: "Communication",
  Cf: "Confidence",
  G: "Grammar",
  Cl: "Clarity",
} as const;

function Bubble({
  role,
  kind,
  children,
}: {
  role: "interviewer" | "candidate";
  kind?: string;
  children: React.ReactNode;
}) {
  const isInterviewer = role === "interviewer";
  const isHint = kind === "hint";

  return (
    <div className={cn("flex", isInterviewer ? "justify-start" : "justify-end")}>
      <div
        className={cn(
          "max-w-[86%] px-4 py-3 text-sm leading-relaxed",
          isInterviewer
            ? "rounded-lg rounded-bl-sm bg-surface-3 text-ink"
            : "rounded-lg rounded-br-sm bg-accent text-white",
          isHint && "border border-warn/30 bg-warn-dim text-ink",
        )}
      >
        {isHint && (
          <span className="mb-1.5 flex items-center gap-1.5 text-[0.6875rem] font-medium text-warn">
            <Lightbulb className="h-3 w-3" />
            Hint
          </span>
        )}
        {kind === "follow_up" && (
          <span className="mb-1.5 block text-[0.6875rem] font-medium text-accent-bright">
            Follow-up
          </span>
        )}
        {children}
      </div>
    </div>
  );
}

function ThinkingIndicator({ stage }: { stage: "evaluating" | "deciding" }) {
  return (
    <div className="flex items-center gap-2.5 text-sm text-ink-tertiary">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="thinking-dot h-1.5 w-1.5 rounded-full bg-ink-tertiary"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </span>
      {stage === "evaluating" ? "Evaluating your answer…" : "Deciding what to ask next…"}
    </div>
  );
}

function ConnectingSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-1/3 rounded-sm" />
      <Skeleton className="h-20 w-[70%] rounded-lg" />
      <p className="pt-1 text-xs text-ink-faint">Connecting to your interviewer…</p>
    </div>
  );
}

/* ------------------------------------------------------------------- hooks */

/** mm:ss since the session became live. */
function useElapsed(running: boolean): string {
  const [seconds, setSeconds] = useState(0);
  const startedRef = useRef<number | null>(null);

  useEffect(() => {
    if (!running) return;
    startedRef.current ??= Date.now();
    const id = window.setInterval(() => {
      setSeconds(Math.floor((Date.now() - (startedRef.current ?? Date.now())) / 1000));
    }, 1000);
    return () => window.clearInterval(id);
  }, [running]);

  const mins = Math.floor(seconds / 60);
  return `${mins}:${String(seconds % 60).padStart(2, "0")}`;
}

/** Feature 8 — record a clip, send it to /api/voice/transcribe, drop the text in the box. */
function useVoiceAnswer(onTranscript: (text: string) => void) {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function toggleRecording() {
    setVoiceError(null);

    if (recording) {
      recorderRef.current?.stop();
      setRecording(false);
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setVoiceError("This browser does not support microphone capture.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (blob.size === 0) return;

        setTranscribing(true);
        try {
          const { text } = await api.transcribe(blob);
          if (text) onTranscript(text);
        } catch (err) {
          setVoiceError(
            err instanceof Error ? err.message : "Transcription failed — type your answer instead.",
          );
        } finally {
          setTranscribing(false);
        }
      };

      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
    } catch {
      setVoiceError("Microphone permission was denied.");
    }
  }

  return { recording, toggleRecording, transcribing, voiceError };
}
