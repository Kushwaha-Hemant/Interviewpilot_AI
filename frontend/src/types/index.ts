// Mirrors backend/app/schemas/api.py — keep the two in sync when the API changes.

export type InterviewMode = "hr" | "technical" | "coding" | "system_design";
export type Difficulty = "easy" | "medium" | "hard";
export type InterviewStatus = "created" | "in_progress" | "completed" | "abandoned";
export type TurnKind = "question" | "follow_up" | "hint";
export type ParseStatus = "pending" | "ready" | "failed";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_recruiter: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/** Register/resend response when the account still needs an emailed code. */
export interface VerificationRequired {
  status: "verification_required";
  email: string;
  expires_in_minutes: number;
  /** "console" means the backend is logging codes instead of emailing them. */
  delivery: "email" | "console";
}

export type RegisterResult = TokenResponse | VerificationRequired;

export function needsVerification(result: RegisterResult): result is VerificationRequired {
  return (result as VerificationRequired).status === "verification_required";
}

export interface Skill {
  name: string;
  category: string;
  proficiency: string;
}

export interface ResumeProfile {
  full_name: string;
  headline: string;
  years_of_experience: number;
  skills: Skill[];
  projects: { name: string; description: string; technologies: string[]; impact: string }[];
  experience: {
    company: string;
    title: string;
    duration: string;
    highlights: string[];
    technologies: string[];
  }[];
  education: {
    institution: string;
    degree: string;
    field_of_study: string;
    year: string;
    score: string;
  }[];
  achievements: string[];
  certifications: string[];
  target_roles: string[];
}

export interface Resume {
  id: string;
  filename: string;
  parse_status: ParseStatus;
  parsed: ResumeProfile | null;
  parse_error: string | null;
  created_at: string;
}

export interface JobProfile {
  title: string;
  company: string;
  seniority: string;
  min_years_experience: number;
  required_skills: { name: string; importance: "must_have" | "nice_to_have" }[];
  responsibilities: string[];
  keywords: string[];
  domain: string;
}

export interface Job {
  id: string;
  title: string | null;
  company: string | null;
  parse_status: ParseStatus;
  parsed: JobProfile | null;
  parse_error: string | null;
  created_at: string;
}

export interface Evaluation {
  technical_score: number;
  communication: number;
  confidence: number;
  grammar: number;
  clarity: number;
  overall: number;
  feedback: string;
  covered_points: string[];
  missed_points: string[];
  red_flags: string[];
}

export interface Turn {
  id: string;
  sequence: number;
  kind: TurnKind;
  question: string;
  skill_tag: string | null;
  answer: string | null;
  evaluation: Evaluation | null;
  overall_score: number | null;
  created_at: string;
}

export interface Interview {
  id: string;
  mode: InterviewMode;
  role: string;
  company: string;
  difficulty: Difficulty;
  status: InterviewStatus;
  planned_questions: number;
  questions_asked: number;
  focus_skills: string[] | null;
  overall_score: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface InterviewDetail extends Interview {
  turns: Turn[];
}

export interface InterviewCreate {
  mode: InterviewMode;
  role: string;
  company: string;
  difficulty: Difficulty;
  planned_questions: number;
  resume_id?: string | null;
  job_id?: string | null;
}

export interface Report {
  id: string;
  interview_id: string;
  summary: string;
  technical_score: number | null;
  communication_score: number | null;
  confidence_score: number | null;
  grammar_score: number | null;
  clarity_score: number | null;
  overall_score: number | null;
  strengths: string[] | null;
  weaknesses: string[] | null;
  mistakes: { topic: string; what_went_wrong: string; correct_answer: string }[] | null;
  recommendations: { topic: string; why: string; resources: string[] }[] | null;
  learning_plan: { week: number; focus: string; tasks: string[]; mini_project: string }[] | null;
  skill_breakdown: { skill: string; score: number }[] | null;
  readiness_percent: number | null;
  readiness_role: string | null;
  estimated_prep_time: string | null;
  created_at: string;
}

export interface SkillStat {
  skill: string;
  score: number;
  attempts: number;
}

export interface TimelinePoint {
  date: string;
  score: number;
  mode: string;
  interview_id: string;
}

export interface Dashboard {
  total_interviews: number;
  completed_interviews: number;
  average_score: number | null;
  practice_streak_days: number;
  strong_skills: SkillStat[];
  weak_skills: SkillStat[];
  timeline: TimelinePoint[];
  confidence_trend: TimelinePoint[];
  ai_recommendation: string | null;
  focus_skill: string | null;
}

export interface CompanyStyle {
  id: string;
  label: string;
  style: string;
}

// ---- WebSocket frames (see backend/app/websocket/interview_ws.py)

export type ServerFrame =
  | { type: "connected"; interview: Interview; turn: Turn | null }
  | { type: "speaking"; kind: TurnKind }
  | { type: "delta"; text: string }
  | { type: "turn"; turn: Turn }
  | { type: "thinking"; stage: "evaluating" | "deciding" }
  | { type: "evaluation"; turn_id: string; evaluation: Evaluation }
  | { type: "completed"; interview_id: string }
  | { type: "error"; detail: string }
  | { type: "pong" };

export type ClientFrame =
  | { type: "answer"; text: string; duration_seconds?: number }
  | { type: "finish" }
  | { type: "ping" };
