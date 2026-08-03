/**
 * Values that both the frontend and backend must agree on.
 *
 * The backend equivalents live in backend/app/models/enums.py — when you add a mode or
 * a company, change both.
 */

export const INTERVIEW_MODES = ["hr", "technical", "coding", "system_design"] as const;
export const DIFFICULTIES = ["easy", "medium", "hard"] as const;
export const INTERVIEW_STATUSES = ["created", "in_progress", "completed", "abandoned"] as const;
export const TURN_KINDS = ["question", "follow_up", "hint"] as const;

export const COMPANIES = [
  "google",
  "amazon",
  "microsoft",
  "meta",
  "netflix",
  "apple",
  "tcs",
  "infosys",
  "accenture",
  "generic",
] as const;

/** Score dimensions returned by the evaluator for every answer. */
export const SCORE_DIMENSIONS = [
  "technical_score",
  "communication",
  "confidence",
  "grammar",
  "clarity",
  "overall",
] as const;

/** A skill at or above this scores as "strong" on the dashboard. */
export const STRONG_SKILL_THRESHOLD = 75;

/** Engine guardrails, mirrored from backend/app/interview/engine.py. */
export const MAX_CONSECUTIVE_FOLLOW_UPS = 2;
export const MIN_QUESTIONS_BEFORE_END = 2;
