"use client";

import { Meter } from "@/components/ui/primitives";
import { scoreToken } from "@/lib/score";
import type { SkillStat } from "@/types";

/**
 * A short ranked list reads better as labelled bars than as a chart with axes:
 * every value is directly labelled, so no tooltip or legend is needed.
 */
export function SkillBars({ stats, tone }: { stats: SkillStat[]; tone: "strong" | "weak" }) {
  if (stats.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-ink-tertiary">
        {tone === "strong"
          ? "Nothing above 75 yet — keep practising."
          : "No weak spots flagged. Try a harder difficulty."}
      </p>
    );
  }

  return (
    <ul className="space-y-4">
      {stats.map((stat) => (
        <li key={stat.skill}>
          <div className="flex items-baseline justify-between gap-3">
            <span className="truncate text-sm text-ink">{stat.skill}</span>
            <span className="tabular shrink-0 text-sm text-ink-secondary">
              {Math.round(stat.score)}
              <span className="text-ink-faint"> / 100</span>
            </span>
          </div>
          <Meter value={stat.score} tone={scoreToken(stat.score)} className="mt-2" />
          <p className="mt-1 text-[0.6875rem] text-ink-faint">
            {stat.attempts} answer{stat.attempts === 1 ? "" : "s"}
          </p>
        </li>
      ))}
    </ul>
  );
}
