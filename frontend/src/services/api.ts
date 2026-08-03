import type {
  CompanyStyle,
  Dashboard,
  Interview,
  InterviewCreate,
  InterviewDetail,
  Job,
  RegisterResult,
  Report,
  Resume,
  TokenResponse,
  Turn,
  User,
  VerificationRequired,
} from "@/types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const TOKEN_KEY = "interviewpilot.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    /** Raw `detail` string from the API — machine-readable codes like
     *  "email_not_verified" travel here so callers branch on the code, not on
     *  a user-facing message that is free to change. */
    readonly detailCode?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    let detailCode: string | undefined;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
        detailCode = body.detail;
      } else if (Array.isArray(body.detail)) {
        // FastAPI validation errors
        detail = body.detail.map((e: { msg: string }) => e.msg).join(", ");
      }
    } catch {
      // non-JSON error body — keep the status text
    }
    throw new ApiError(detail, response.status, detailCode);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** The backend answers 403 with this detail when an account exists but is unverified. */
export const EMAIL_NOT_VERIFIED = "email_not_verified";

export const api = {
  // ---- auth
  register: (email: string, password: string, full_name?: string) =>
    request<RegisterResult>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: full_name || null }),
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  verifyEmail: (email: string, code: string) =>
    request<TokenResponse>("/api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),
  resendCode: (email: string) =>
    request<VerificationRequired>("/api/auth/resend-code", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  me: () => request<User>("/api/auth/me"),

  // ---- resumes
  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Resume>("/api/resumes", { method: "POST", body: form });
  },
  listResumes: () => request<Resume[]>("/api/resumes"),
  deleteResume: (id: string) => request<void>(`/api/resumes/${id}`, { method: "DELETE" }),

  // ---- jobs
  createJob: (raw_text: string, title?: string, company?: string) =>
    request<Job>("/api/jobs", {
      method: "POST",
      body: JSON.stringify({ raw_text, title: title || null, company: company || null }),
    }),
  listJobs: () => request<Job[]>("/api/jobs"),
  deleteJob: (id: string) => request<void>(`/api/jobs/${id}`, { method: "DELETE" }),

  // ---- interviews
  companies: () => request<CompanyStyle[]>("/api/interviews/companies"),
  createInterview: (payload: InterviewCreate) =>
    request<InterviewDetail>("/api/interviews", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listInterviews: () => request<Interview[]>("/api/interviews"),
  getInterview: (id: string) => request<InterviewDetail>(`/api/interviews/${id}`),
  currentTurn: (id: string) => request<Turn | null>(`/api/interviews/${id}/current-turn`),
  finishInterview: (id: string) =>
    request<Interview>(`/api/interviews/${id}/finish`, { method: "POST" }),

  // ---- reports
  createReport: (id: string) =>
    request<Report>(`/api/interviews/${id}/report`, { method: "POST" }),
  getReport: (id: string) => request<Report>(`/api/interviews/${id}/report`),
  reportPdfUrl: (id: string) => `${API_BASE}/api/interviews/${id}/report.pdf`,

  // ---- dashboard
  dashboard: () => request<Dashboard>("/api/dashboard"),

  // ---- voice
  transcribe: (blob: Blob) => {
    const form = new FormData();
    form.append("file", blob, "answer.webm");
    return request<{ text: string }>("/api/voice/transcribe", { method: "POST", body: form });
  },
};

/** PDF download needs the auth header, so fetch it as a blob rather than linking. */
export async function downloadReportPdf(interviewId: string, filename: string) {
  const token = getToken();
  const response = await fetch(api.reportPdfUrl(interviewId), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new ApiError("Could not download the report", response.status);

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
