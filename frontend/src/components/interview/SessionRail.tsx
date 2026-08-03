"use client";

import { Activity, Clock, ListChecks, Target } from "lucide-react";

import { ScoreRing } from "@/components/ui/ScoreRing";
import { Badge, Card, CardBody } from "@/components/ui/primitives";
import { scoreText } from "@/lib/score";
import { cn } from "@/lib/utils";
import type { Evaluation, Interview } from "@/types";

/**
 * Live session sidebar.
 *
 * Everything here is derived from what already arrived over the socket — the rail never
 * fetches, so it cannot disagree with the transcript beside it.
 */
export function SessionRail({
  interview,
  questionsAsked,
  answered,
  elapsed,
  runningAverage,
  latest,
}: {
  interview: Interview | null;
  questionsAsked: number;
  answered: number;
  elapsed: string;
  runningAverage: number | null;
  latest: Evaluation | null;
}) {
  const planned = interview?.planned_questions ?? 0;

  return (
    <aside className="hidden w-72 shrink-0 space-y-3 xl:block">
      {/* ----------------------------------------------------- progress */}
      <Card>
        <CardBody className="space-y-4">
          <div className="flex items-center gap-2">
            <ListChecks className="h-3.5 w-3.5 text-ink-faint" />
            <span className="text-[0.6875rem] font-medium tracking-wide text-ink-secondary uppercase">
              Progress
            </span>
            <span className="tabular ml-auto text-xs text-ink-tertiary">
              {Math.min(questionsAsked, planned)} / {planned}
            </span>
          </div>

          {/* Segmented rather than a single bar: a candidate wants to know how many
              questions are left, not what fraction is done. */}
          <div className="flex gap-1" role="img" aria-label={`${questionsAsked} of ${planned} questions`}>
            {Array.from({ length: planned }).map((_, index) => (
              <span
                key={index}
                className={cn(
                  "h-1.5 flex-1 rounded-full transition-colors duration-500",
                  index < questionsAsked ? "bg-accent" : "bg-surface-3",
                )}
              />
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3 border-t border-line-subtle pt-3.5">
            <div>
              <div className="flex items-center gap-1.5 text-[0.6875rem] text-ink-faint">
                <Clock className="h-3 w-3" />
                Elapsed
              </div>
              <p className="tabular mt-1 text-lg font-medium">{elapsed}</p>
            </div>
            <div>
              <div className="flex items-center gap-1.5 text-[0.6875rem] text-ink-faint">
                <Activity className="h-3 w-3" />
                Answered
              </div>
              <p className="tabular mt-1 text-lg font-medium">{answered}</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* ------------------------------------------------ running score */}
      <Card>
        <CardBody className="flex flex-col items-center py-6">
          <ScoreRing value={runningAverage} size={116} stroke={8} label="Running avg" />
          {latest ? (
            <div className="mt-5 w-full space-y-2">
              {(
                [
                  ["Technical", latest.technical_score],
                  ["Communication", latest.communication],
                  ["Confidence", latest.confidence],
                  ["Clarity", latest.clarity],
                ] as const
              ).map(([label, value]) => (
                <div key={label} className="flex items-center justify-between text-xs">
                  <span className="text-ink-tertiary">{label}</span>
                  <span className={cn("tabular font-medium", scoreText(value))}>{value}</span>
                </div>
              ))}
              <p className="pt-1 text-center text-[0.625rem] text-ink-faint">Last answer</p>
            </div>
          ) : (
            <p className="mt-4 text-center text-xs text-ink-faint">
              Scores appear after your first answer.
            </p>
          )}
        </CardBody>
      </Card>

      {/* ------------------------------------------------- focus skills */}
      {interview?.focus_skills && interview.focus_skills.length > 0 && (
        <Card>
          <CardBody>
            <div className="flex items-center gap-2">
              <Target className="h-3.5 w-3.5 text-ink-faint" />
              <span className="text-[0.6875rem] font-medium tracking-wide text-ink-secondary uppercase">
                Focus areas
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {interview.focus_skills.slice(0, 8).map((skill) => (
                <Badge key={skill} tone="outline">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </aside>
  );
}
