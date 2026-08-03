"use client";

import {
  ArrowUpRight,
  BarChart3,
  Flame,
  Layers,
  Lightbulb,
  Plus,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { ProgressChart } from "@/components/charts/ProgressChart";
import { SkillBars } from "@/components/charts/SkillBars";
import { SkillRadar } from "@/components/charts/SkillRadar";
import { StatTile } from "@/components/StatTile";
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorMessage,
  Skeleton,
} from "@/components/ui/primitives";
import { scoreText, scoreTone } from "@/lib/score";
import { modeLabel, relativeTime } from "@/lib/utils";
import { api } from "@/services/api";
import type { Dashboard, Interview } from "@/types";

export default function DashboardPage() {
  return (
    <AppShell>
      <DashboardContent />
    </AppShell>
  );
}

function DashboardContent() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [dashboard, history] = await Promise.all([api.dashboard(), api.listInterviews()]);
        if (cancelled) return;
        setData(dashboard);
        setInterviews(history);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <DashboardSkeleton />;

  if (error || !data) {
    return <ErrorMessage>{error ?? "No dashboard data"}</ErrorMessage>;
  }

  const hasHistory = interviews.length > 0;
  const radarData = [...data.strong_skills, ...data.weak_skills]
    .map((s) => ({ skill: s.skill, score: s.score }))
    .slice(0, 8);

  return (
    <div className="animate-fade-up">
      {/* -------------------------------------------------------- header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your progress</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            Every answer you give is scored and folded into these numbers.
          </p>
        </div>
        <Link href="/interview/new">
          <Button>
            <Plus className="h-4 w-4" />
            New interview
          </Button>
        </Link>
      </div>

      {!hasHistory ? (
        <Card className="mt-8">
          <CardBody>
            <EmptyState
              icon={Sparkles}
              title="No interviews yet"
              body="Run your first one to see scores, weak topics, and a readiness verdict. It takes about ten minutes."
              action={
                <Link href="/interview/new">
                  <Button>
                    Start your first interview
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>
                </Link>
              }
              className="border-0 py-6"
            />
          </CardBody>
        </Card>
      ) : (
        <>
          {/* ------------------------------------------- headline numbers */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              label="Interviews"
              value={data.total_interviews}
              icon={Layers}
              hint={`${data.completed_interviews} completed`}
            />
            <StatTile
              label="Average score"
              value={data.average_score == null ? "—" : Math.round(data.average_score)}
              icon={BarChart3}
              valueClassName={scoreText(data.average_score)}
              hint="Across completed interviews"
              accessory={
                data.average_score != null ? (
                  <Badge tone={scoreTone(data.average_score)}>/ 100</Badge>
                ) : undefined
              }
            />
            <StatTile
              label="Practice streak"
              value={`${data.practice_streak_days}d`}
              icon={Flame}
              hint={
                data.practice_streak_days > 0
                  ? "Keep it going — practise again today"
                  : "Practise today to start one"
              }
            />
            <StatTile
              label="Skills tracked"
              value={data.strong_skills.length + data.weak_skills.length}
              icon={Target}
              hint={data.focus_skill ? `Focus: ${data.focus_skill}` : "Add a resume for sharper focus"}
            />
          </div>

          {/* ----------------------------------------- AI recommendation */}
          {data.ai_recommendation && (
            <Card className="mt-4 border-accent-line bg-gradient-to-r from-accent-dim to-transparent">
              <CardBody className="flex gap-3.5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent-dim">
                  <Lightbulb className="h-4 w-4 text-accent-bright" />
                </span>
                <div className="min-w-0">
                  <p className="text-[0.6875rem] font-medium tracking-wide text-accent-bright uppercase">
                    Your next move
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-ink">{data.ai_recommendation}</p>
                </div>
              </CardBody>
            </Card>
          )}

          {/* ------------------------------------------------------ charts */}
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <TrendingUp className="h-3.5 w-3.5 text-ink-faint" />
                <CardTitle>Score &amp; confidence over time</CardTitle>
              </CardHeader>
              <CardBody className="pt-3">
                <ProgressChart timeline={data.timeline} confidence={data.confidence_trend} />
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <Target className="h-3.5 w-3.5 text-ink-faint" />
                <CardTitle>Skill radar</CardTitle>
              </CardHeader>
              <CardBody className="pt-3">
                <SkillRadar data={radarData} />
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <Flame className="h-3.5 w-3.5 text-good" />
                <CardTitle>Strong skills</CardTitle>
              </CardHeader>
              <CardBody className="pt-4">
                <SkillBars stats={data.strong_skills} tone="strong" />
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <Target className="h-3.5 w-3.5 text-warn" />
                <CardTitle>Weak topics</CardTitle>
              </CardHeader>
              <CardBody className="pt-4">
                <SkillBars stats={data.weak_skills} tone="weak" />
              </CardBody>
            </Card>
          </div>
        </>
      )}

      {/* ------------------------------------------------------- history */}
      {hasHistory && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Interview history</CardTitle>
            <span className="ml-auto text-xs text-ink-faint">{interviews.length} total</span>
          </CardHeader>
          <CardBody className="pt-3">
            <div className="-mx-2 overflow-x-auto">
              <table className="w-full min-w-[38rem] text-sm">
                <thead>
                  <tr className="border-b border-line-subtle text-left text-[0.6875rem] tracking-wider text-ink-faint uppercase">
                    <th className="px-2 pb-2.5 font-medium">Role</th>
                    <th className="px-2 pb-2.5 font-medium">Mode</th>
                    <th className="px-2 pb-2.5 font-medium">Style</th>
                    <th className="px-2 pb-2.5 font-medium">When</th>
                    <th className="px-2 pb-2.5 text-right font-medium">Score</th>
                    <th className="px-2 pb-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-line-subtle">
                  {interviews.map((interview) => (
                    <tr key={interview.id} className="group transition-colors hover:bg-surface-2/50">
                      <td className="px-2 py-3 font-medium text-ink">{interview.role}</td>
                      <td className="px-2 py-3">
                        <Badge tone="outline">{modeLabel(interview.mode)}</Badge>
                      </td>
                      <td className="px-2 py-3 text-ink-tertiary capitalize">{interview.company}</td>
                      <td className="px-2 py-3 whitespace-nowrap text-ink-tertiary">
                        {relativeTime(interview.created_at)}
                      </td>
                      <td className="px-2 py-3 text-right">
                        <span className={`tabular font-medium ${scoreText(interview.overall_score)}`}>
                          {interview.overall_score == null
                            ? "—"
                            : Math.round(interview.overall_score)}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-right">
                        <Link
                          href={
                            interview.status === "completed"
                              ? `/report/${interview.id}`
                              : `/interview/${interview.id}`
                          }
                          className="inline-flex items-center gap-1 text-xs text-ink-tertiary transition-colors group-hover:text-accent-bright"
                        >
                          {interview.status === "completed" ? "Report" : "Resume"}
                          <ArrowUpRight className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div>
      <Skeleton className="h-8 w-48" />
      <Skeleton className="mt-2 h-4 w-80" />

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-[7.5rem] rounded-lg" />
        ))}
      </div>

      <Skeleton className="mt-4 h-20 rounded-lg" />

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-[22rem] rounded-lg" />
        ))}
      </div>
    </div>
  );
}
