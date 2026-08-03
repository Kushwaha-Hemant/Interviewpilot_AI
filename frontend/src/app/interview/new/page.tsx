"use client";

import {
  Braces,
  Check,
  FileText,
  Loader2,
  Network,
  Terminal,
  Upload,
  UserRound,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
  Badge,
  Button,
  Card,
  CardBody,
  ErrorMessage,
  Field,
  Input,
  Select,
  Textarea,
} from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { api } from "@/services/api";
import type { CompanyStyle, Difficulty, InterviewMode, Job, Resume } from "@/types";

const MODES: {
  value: InterviewMode;
  label: string;
  blurb: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  {
    value: "hr",
    label: "HR / Behavioural",
    blurb: "Motivation, conflict, ownership — STAR answers",
    icon: UserRound,
  },
  {
    value: "technical",
    label: "Technical",
    blurb: "Concepts and applied questions on your stack",
    icon: Braces,
  },
  {
    value: "coding",
    label: "Coding",
    blurb: "DSA problems — approach, complexity, then code",
    icon: Terminal,
  },
  {
    value: "system_design",
    label: "System design",
    blurb: "Open design briefs with real scale numbers",
    icon: Network,
  },
];

export default function NewInterviewPage() {
  return (
    <AppShell>
      <NewInterviewForm />
    </AppShell>
  );
}

function NewInterviewForm() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);

  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [companies, setCompanies] = useState<CompanyStyle[]>([]);

  const [resumeId, setResumeId] = useState("");
  const [jobId, setJobId] = useState("");
  const [jobText, setJobText] = useState("");

  const [mode, setMode] = useState<InterviewMode>("technical");
  const [role, setRole] = useState("Backend Engineer");
  const [company, setCompany] = useState("generic");
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [questions, setQuestions] = useState(6);

  const [uploading, setUploading] = useState(false);
  const [savingJob, setSavingJob] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [r, j, c] = await Promise.all([api.listResumes(), api.listJobs(), api.companies()]);
        setResumes(r);
        setJobs(j);
        setCompanies(c);
        if (r[0]) setResumeId(r[0].id);
        if (j[0]) setJobId(j[0].id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load your saved data");
      }
    })();
  }, []);

  async function handleUpload(file: File) {
    setError(null);
    setUploading(true);
    try {
      const resume = await api.uploadResume(file);
      setResumes((prev) => [resume, ...prev]);
      setResumeId(resume.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleSaveJob() {
    if (jobText.trim().length < 40) {
      setError("Paste a bit more of the job description (at least 40 characters).");
      return;
    }
    setError(null);
    setSavingJob(true);
    try {
      const job = await api.createJob(jobText);
      setJobs((prev) => [job, ...prev]);
      setJobId(job.id);
      setJobText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the job description");
    } finally {
      setSavingJob(false);
    }
  }

  async function handleStart() {
    setError(null);
    setStarting(true);
    try {
      const interview = await api.createInterview({
        mode,
        role,
        company,
        difficulty,
        planned_questions: questions,
        resume_id: resumeId || null,
        job_id: jobId || null,
      });
      router.push(`/interview/${interview.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the interview");
      setStarting(false);
    }
  }

  const selectedResume = resumes.find((r) => r.id === resumeId);
  const selectedJob = jobs.find((j) => j.id === jobId);

  return (
    <div className="animate-fade-up mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold tracking-tight">Set up your interview</h1>
      <p className="mt-1 text-sm text-ink-secondary">
        The more context you give, the closer the questions get to the real ones.
      </p>

      {/* ------------------------------------------------------ 1. resume */}
      <Step index={1} title="Resume" hint="Optional — but this is what makes questions personal">
        <input
          ref={fileInput}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleUpload(file);
            event.target.value = "";
          }}
        />

        {selectedResume?.parsed ? (
          <div className="rounded-md border border-good/25 bg-good-dim p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Check className="h-4 w-4 shrink-0 text-good" />
              <span className="text-sm font-medium">{selectedResume.filename}</span>
              <Badge tone="good">{selectedResume.parsed.skills.length} skills</Badge>
              <button
                type="button"
                onClick={() => setResumeId("")}
                className="ml-auto text-ink-tertiary transition-colors hover:text-ink"
                aria-label="Use no resume"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {selectedResume.parsed.skills.slice(0, 14).map((skill) => (
                <Badge key={skill.name} tone="outline">
                  {skill.name}
                </Badge>
              ))}
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={uploading}
            className="flex w-full flex-col items-center justify-center rounded-md border border-dashed border-line px-6 py-8 transition-colors hover:border-accent-line hover:bg-accent-dim/40 disabled:opacity-60"
          >
            {uploading ? (
              <Loader2 className="h-5 w-5 animate-spin text-accent-bright" />
            ) : (
              <Upload className="h-5 w-5 text-ink-tertiary" />
            )}
            <span className="mt-2.5 text-sm font-medium">
              {uploading ? "Reading your resume…" : "Upload a PDF resume"}
            </span>
            <span className="mt-0.5 text-xs text-ink-faint">
              {uploading ? "Extracting skills, projects and experience" : "Text-based PDF, up to 10 MB"}
            </span>
          </button>
        )}

        {resumes.length > 0 && (
          <Select
            value={resumeId}
            onChange={(e) => setResumeId(e.target.value)}
            className="mt-3"
            aria-label="Choose a saved resume"
          >
            <option value="">No resume</option>
            {resumes.map((resume) => (
              <option key={resume.id} value={resume.id}>
                {resume.filename}
              </option>
            ))}
          </Select>
        )}

        {selectedResume?.parse_status === "failed" && (
          <p className="mt-3 text-sm text-warn">Extraction failed: {selectedResume.parse_error}</p>
        )}
      </Step>

      {/* --------------------------------------------------------- 2. JD */}
      <Step index={2} title="Job description" hint="Optional — targets the questions at the role">
        {selectedJob?.parsed ? (
          <div className="rounded-md border border-good/25 bg-good-dim p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Check className="h-4 w-4 shrink-0 text-good" />
              <span className="text-sm font-medium">
                {selectedJob.title ?? "Untitled role"}
                {selectedJob.company ? ` — ${selectedJob.company}` : ""}
              </span>
              <button
                type="button"
                onClick={() => setJobId("")}
                className="ml-auto text-ink-tertiary transition-colors hover:text-ink"
                aria-label="Use no job description"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {selectedJob.parsed.required_skills.slice(0, 12).map((skill) => (
                <Badge key={skill.name} tone={skill.importance === "must_have" ? "accent" : "outline"}>
                  {skill.name}
                </Badge>
              ))}
            </div>
          </div>
        ) : (
          <>
            <Textarea
              rows={5}
              placeholder="Paste a job description — we'll pull out the required skills, responsibilities and ATS keywords…"
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
            />
            <Button
              variant="secondary"
              size="sm"
              className="mt-3"
              onClick={handleSaveJob}
              loading={savingJob}
              disabled={jobText.trim().length === 0}
            >
              {!savingJob && <FileText className="h-3.5 w-3.5" />}
              {savingJob ? "Extracting…" : "Save & extract"}
            </Button>
          </>
        )}

        {jobs.length > 0 && !selectedJob && (
          <Select
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            className="mt-3"
            aria-label="Choose a saved job description"
          >
            <option value="">No job description</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title ?? "Untitled"} {job.company ? `— ${job.company}` : ""}
              </option>
            ))}
          </Select>
        )}
      </Step>

      {/* ------------------------------------------------------ 3. format */}
      <Step index={3} title="Format" hint="What kind of round is this?">
        <div className="grid gap-2.5 sm:grid-cols-2">
          {MODES.map((option) => {
            const active = mode === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setMode(option.value)}
                aria-pressed={active}
                className={cn(
                  "flex gap-3 rounded-md border p-3.5 text-left transition-all duration-150",
                  active
                    ? "border-accent bg-accent-dim shadow-[0_0_0_1px_var(--color-accent)]"
                    : "border-line-subtle hover:border-line hover:bg-surface-2/60",
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-sm",
                    active ? "bg-accent/20" : "bg-surface-3",
                  )}
                >
                  <option.icon
                    className={cn("h-4 w-4", active ? "text-accent-bright" : "text-ink-tertiary")}
                  />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-medium">{option.label}</span>
                  <span className="mt-0.5 block text-xs leading-snug text-ink-tertiary">
                    {option.blurb}
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field label="Target role" htmlFor="role">
            <Input id="role" value={role} onChange={(e) => setRole(e.target.value)} />
          </Field>

          <Field label="Company style" htmlFor="company" hint="Changes how they interview">
            <Select id="company" value={company} onChange={(e) => setCompany(e.target.value)}>
              {companies.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Difficulty" htmlFor="difficulty">
            <Select
              id="difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as Difficulty)}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </Select>
          </Field>

          <Field
            label="Questions"
            htmlFor="questions"
            hint={`${questions} · ~${questions * 2} min`}
          >
            <input
              id="questions"
              type="range"
              min={2}
              max={12}
              value={questions}
              onChange={(e) => setQuestions(Number(e.target.value))}
              className="mt-3 w-full accent-[var(--color-accent)]"
            />
            <p className="text-xs text-ink-faint">
              Follow-ups and hints are extra — they don&apos;t count toward this.
            </p>
          </Field>
        </div>
      </Step>

      <div className="mt-6">
        <ErrorMessage>{error}</ErrorMessage>
      </div>

      <div className="sticky bottom-0 -mx-6 mt-4 border-t border-line-subtle bg-canvas/80 px-6 py-4 backdrop-blur-xl">
        <Button size="lg" className="w-full" onClick={handleStart} loading={starting}>
          {starting ? "Preparing your first question…" : "Start interview"}
        </Button>
      </div>
    </div>
  );
}

function Step({
  index,
  title,
  hint,
  children,
}: {
  index: number;
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="mt-5">
      <CardBody>
        <div className="mb-4 flex items-baseline gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line bg-surface-2 text-xs font-medium text-ink-secondary">
            {index}
          </span>
          <div>
            <h2 className="text-sm font-medium">{title}</h2>
            <p className="mt-0.5 text-xs text-ink-tertiary">{hint}</p>
          </div>
        </div>
        {children}
      </CardBody>
    </Card>
  );
}
