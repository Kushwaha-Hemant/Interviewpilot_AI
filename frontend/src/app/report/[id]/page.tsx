"use client";

import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  Download,
  GraduationCap,
  MessageSquare,
  Target,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { use, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { SkillRadar } from "@/components/charts/SkillRadar";
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  ErrorMessage,
  Meter,
  Skeleton,
} from "@/components/ui/primitives";
import { ScoreRing } from "@/components/ui/ScoreRing";
import { scoreLabel, scoreText, scoreToken, scoreTone } from "@/lib/score";
import { cn, modeLabel } from "@/lib/utils";
import { ApiError, api, downloadReportPdf } from "@/services/api";
import type { InterviewDetail, Report } from "@/types";

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <AppShell>
      <ReportView interviewId={id} />
    </AppShell>
  );
}

function ReportView({ interviewId }: { interviewId: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [interview, setInterview] = useState<InterviewDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const detail = await api.getInterview(interviewId);
        if (!cancelled) setInterview(detail);

        let data: Report;
        try {
          data = await api.getReport(interviewId);
        } catch (err) {
          // A 404 just means it hasn't been generated yet — do it now.
          if (err instanceof ApiError && err.status === 404) {
            data = await api.createReport(interviewId);
          } else {
            throw err;
          }
        }
        if (!cancelled) setReport(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load the report");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [interviewId]);

  async function handleDownload() {
    setDownloading(true);
    try {
      await downloadReportPdf(interviewId, `interviewpilot-report-${interviewId.slice(0, 8)}.pdf`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <ReportSkeleton />;

  if (error || !report) {
    return (
      <div>
        <ErrorMessage>{error ?? "No report available"}</ErrorMessage>
        <Link href="/dashboard" className="mt-4 inline-block text-sm text-accent-bright">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const dimensions = [
    { label: "Technical", value: report.technical_score },
    { label: "Communication", value: report.communication_score },
    { label: "Confidence", value: report.confidence_score },
    { label: "Grammar", value: report.grammar_score },
    { label: "Clarity", value: report.clarity_score },
  ];

  return (
    <div className="animate-fade-up">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary transition-colors hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Dashboard
      </Link>

      {/* ---------------------------------------------------------- hero */}
      <Card className="mt-4 overflow-hidden">
        <CardBody className="flex flex-wrap items-center gap-8 p-7">
          <ScoreRing value={report.overall_score} label="Overall" size={140} />

          <div className="min-w-56 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Interview report</h1>
              <Badge tone={scoreTone(report.overall_score)}>{scoreLabel(report.overall_score)}</Badge>
            </div>
            {interview && (
              <p className="mt-1.5 text-sm text-ink-secondary">
                {interview.role} · {modeLabel(interview.mode)} ·{" "}
                <span className="capitalize">{interview.company}</span> style ·{" "}
                {interview.turns.filter((t) => t.answer).length} answers
              </p>
            )}

            <div className="mt-5 flex flex-wrap gap-8">
              <div>
                <p className="text-[0.6875rem] tracking-wide text-ink-faint uppercase">Readiness</p>
                <p
                  className={cn(
                    "tabular mt-1 text-2xl font-semibold",
                    scoreText(report.readiness_percent),
                  )}
                >
                  {report.readiness_percent == null
                    ? "—"
                    : `${Math.round(report.readiness_percent)}%`}
                </p>
                {report.readiness_role && (
                  <p className="mt-0.5 max-w-48 text-xs text-ink-tertiary">
                    for {report.readiness_role}
                  </p>
                )}
              </div>
              <div>
                <p className="text-[0.6875rem] tracking-wide text-ink-faint uppercase">
                  Estimated prep
                </p>
                <p className="mt-1 text-2xl font-semibold">{report.estimated_prep_time ?? "—"}</p>
                <p className="mt-0.5 text-xs text-ink-tertiary">at ~8 hours a week</p>
              </div>
            </div>
          </div>

          <Button variant="outline" onClick={handleDownload} loading={downloading}>
            <Download className="h-4 w-4" />
            Download PDF
          </Button>
        </CardBody>
      </Card>

      {/* ------------------------------------------- breakdown + summary */}
      <div className="mt-4 grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Score breakdown</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4 pt-4">
            {dimensions.map((dimension) => (
              <div key={dimension.label}>
                <div className="flex items-baseline justify-between">
                  <span className="text-sm text-ink-secondary">{dimension.label}</span>
                  <span className={cn("tabular text-sm font-medium", scoreText(dimension.value))}>
                    {dimension.value == null ? "—" : Math.round(dimension.value)}
                  </span>
                </div>
                <Meter
                  value={dimension.value ?? 0}
                  tone={scoreToken(dimension.value)}
                  className="mt-1.5"
                />
              </div>
            ))}
          </CardBody>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <MessageSquare className="h-3.5 w-3.5 text-ink-faint" />
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardBody className="pt-3">
            <p className="text-sm leading-relaxed text-ink-secondary">{report.summary}</p>
          </CardBody>
        </Card>
      </div>

      {/* ------------------------------------ radar + strengths/weaknesses */}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <Target className="h-3.5 w-3.5 text-ink-faint" />
            <CardTitle>Skills probed</CardTitle>
          </CardHeader>
          <CardBody className="pt-3">
            <SkillRadar data={report.skill_breakdown ?? []} />
          </CardBody>
        </Card>

        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <TrendingUp className="h-3.5 w-3.5 text-good" />
              <CardTitle>Strengths</CardTitle>
            </CardHeader>
            <CardBody className="pt-3">
              <BulletList items={report.strengths} tone="good" empty="None recorded." />
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <Target className="h-3.5 w-3.5 text-warn" />
              <CardTitle>Areas to improve</CardTitle>
            </CardHeader>
            <CardBody className="pt-3">
              <BulletList items={report.weaknesses} tone="warn" empty="Nothing flagged." />
            </CardBody>
          </Card>
        </div>
      </div>

      {/* ------------------------------------------------------ mistakes */}
      {report.mistakes && report.mistakes.length > 0 && (
        <Card className="mt-4">
          <CardHeader>
            <AlertTriangle className="h-3.5 w-3.5 text-bad" />
            <CardTitle>Mistakes to correct</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3 pt-3">
            {report.mistakes.map((mistake) => (
              <div
                key={mistake.topic}
                className="rounded-md border border-line-subtle bg-surface-2/40 p-4"
              >
                <p className="text-sm font-medium">{mistake.topic}</p>
                <p className="mt-1.5 flex gap-2 text-sm leading-relaxed text-ink-secondary">
                  <span className="mt-0.5 shrink-0 text-bad">✗</span>
                  {mistake.what_went_wrong}
                </p>
                <p className="mt-1.5 flex gap-2 text-sm leading-relaxed text-ink-secondary">
                  <span className="mt-0.5 shrink-0 text-good">✓</span>
                  {mistake.correct_answer}
                </p>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {/* ------------------------------------------------ recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <Card className="mt-4">
          <CardHeader>
            <BookOpen className="h-3.5 w-3.5 text-ink-faint" />
            <CardTitle>What to study</CardTitle>
          </CardHeader>
          <CardBody className="grid gap-3 pt-3 sm:grid-cols-2">
            {report.recommendations.map((rec) => (
              <div key={rec.topic} className="rounded-md border border-line-subtle bg-surface-2/40 p-4">
                <p className="text-sm font-medium">{rec.topic}</p>
                <p className="mt-1 text-xs leading-relaxed text-ink-tertiary">{rec.why}</p>
                {rec.resources.length > 0 && (
                  <ul className="mt-2.5 space-y-1 border-t border-line-subtle pt-2.5">
                    {rec.resources.map((resource) => (
                      <li key={resource} className="text-xs text-accent-bright">
                        {resource}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {/* ------------------------------------------------- learning plan */}
      {report.learning_plan && report.learning_plan.length > 0 && (
        <Card className="mt-4">
          <CardHeader>
            <GraduationCap className="h-3.5 w-3.5 text-accent-bright" />
            <CardTitle>Your plan</CardTitle>
          </CardHeader>
          <CardBody className="pt-4">
            <ol className="space-y-6">
              {report.learning_plan.map((step, index) => (
                <li key={step.week} className="relative flex gap-4">
                  {/* Connector line between weeks, stopping at the last one. */}
                  {index < report.learning_plan!.length - 1 && (
                    <span className="absolute top-8 left-[0.9375rem] h-full w-px bg-line" aria-hidden />
                  )}
                  <span className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-accent-line bg-accent-dim text-xs font-semibold text-accent-bright">
                    {step.week}
                  </span>
                  <div className="min-w-0 flex-1 pb-1">
                    <p className="text-sm font-medium">{step.focus}</p>
                    <ul className="mt-1.5 space-y-1">
                      {step.tasks.map((task) => (
                        <li key={task} className="flex gap-2 text-sm text-ink-secondary">
                          <span className="text-ink-faint">·</span>
                          {task}
                        </li>
                      ))}
                    </ul>
                    {step.mini_project && (
                      <p className="mt-2 inline-flex rounded-sm bg-surface-2 px-2.5 py-1 text-xs text-accent-bright">
                        Build: {step.mini_project}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </CardBody>
        </Card>
      )}

      {/* ----------------------------------------------------- transcript */}
      {interview && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Full transcript</CardTitle>
            <span className="ml-auto text-xs text-ink-faint">{interview.turns.length} turns</span>
          </CardHeader>
          <CardBody className="space-y-5 pt-4">
            {interview.turns.map((turn) => (
              <div key={turn.id} className="border-l-2 border-line pl-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={turn.kind === "hint" ? "warn" : turn.kind === "follow_up" ? "accent" : "outline"}>
                    {modeLabel(turn.kind)}
                  </Badge>
                  {turn.skill_tag && (
                    <span className="text-xs text-ink-faint">{turn.skill_tag}</span>
                  )}
                  {turn.evaluation && (
                    <span
                      className={cn(
                        "tabular ml-auto text-xs font-medium",
                        scoreText(turn.evaluation.overall),
                      )}
                    >
                      {turn.evaluation.overall}/100
                    </span>
                  )}
                </div>

                <p className="mt-2 text-sm leading-relaxed text-ink">{turn.question}</p>

                {turn.answer && (
                  <p className="mt-2.5 rounded-sm bg-surface-2/50 p-3 text-sm leading-relaxed text-ink-secondary">
                    {turn.answer}
                  </p>
                )}
                {turn.evaluation && (
                  <p className="mt-2 text-xs leading-relaxed text-ink-tertiary">
                    {turn.evaluation.feedback}
                  </p>
                )}
              </div>
            ))}
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function BulletList({
  items,
  tone,
  empty,
}: {
  items: string[] | null;
  tone: "good" | "warn";
  empty: string;
}) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-ink-tertiary">{empty}</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item} className="flex gap-2.5 text-sm leading-relaxed text-ink-secondary">
          <span
            className={cn(
              "mt-1.5 h-1 w-1 shrink-0 rounded-full",
              tone === "good" ? "bg-good" : "bg-warn",
            )}
          />
          {item}
        </li>
      ))}
    </ul>
  );
}

function ReportSkeleton() {
  return (
    <div>
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-4 h-52 rounded-lg" />
      <div className="mt-4 grid gap-4 lg:grid-cols-5">
        <Skeleton className="h-64 rounded-lg lg:col-span-2" />
        <Skeleton className="h-64 rounded-lg lg:col-span-3" />
      </div>
      <p className="mt-6 text-center text-sm text-ink-tertiary">
        Writing your report — this takes a moment on a reasoning model.
      </p>
    </div>
  );
}
