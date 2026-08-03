/**
 * Score → colour band.
 *
 * One source of truth so a 72 looks the same on the dashboard, in the interview room,
 * and on the report. Bands mirror the evaluator's own calibration in
 * backend/app/prompts/evaluator.py.
 */

export type ScoreBand = "strong" | "solid" | "fair" | "weak" | "none";

export function scoreBand(score: number | null | undefined): ScoreBand {
  if (score == null) return "none";
  if (score >= 85) return "strong";
  if (score >= 70) return "solid";
  if (score >= 55) return "fair";
  return "weak";
}

/** CSS custom-property value — for SVG strokes and inline styles. */
export function scoreToken(score: number | null | undefined): string {
  return {
    strong: "var(--color-good)",
    solid: "var(--color-info)",
    fair: "var(--color-warn)",
    weak: "var(--color-bad)",
    none: "var(--color-ink-faint)",
  }[scoreBand(score)];
}

/** Tailwind text class. */
export function scoreText(score: number | null | undefined): string {
  return {
    strong: "text-good",
    solid: "text-info",
    fair: "text-warn",
    weak: "text-bad",
    none: "text-ink-faint",
  }[scoreBand(score)];
}

/** Badge tone matching the band. */
export function scoreTone(score: number | null | undefined) {
  return (
    {
      strong: "good",
      solid: "info",
      fair: "warn",
      weak: "bad",
      none: "default",
    } as const
  )[scoreBand(score)];
}

export function scoreLabel(score: number | null | undefined): string {
  return {
    strong: "Strong",
    solid: "Solid",
    fair: "Needs work",
    weak: "Weak",
    none: "Unscored",
  }[scoreBand(score)];
}
