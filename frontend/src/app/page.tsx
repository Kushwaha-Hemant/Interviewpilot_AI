"use client";

import {
  ArrowRight,
  BarChart3,
  Brain,
  FileText,
  Gauge,
  Mic,
  Building2,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { Badge, Button } from "@/components/ui/primitives";
import { useAuthStore } from "@/store/auth";

const FEATURES = [
  {
    icon: FileText,
    title: "Resume-aware questions",
    body: "Upload a PDF and paste the job spec. Questions come from the overlap and the gaps — never a static bank.",
  },
  {
    icon: Brain,
    title: "It actually pushes back",
    body: "Every answer is evaluated, then the interviewer decides: probe deeper, offer a hint, or move on.",
  },
  {
    icon: BarChart3,
    title: "Six scoring dimensions",
    body: "Technical accuracy, communication, confidence, grammar, clarity and an overall verdict — per answer.",
  },
  {
    icon: Building2,
    title: "Company interview styles",
    body: "Amazon leans on Leadership Principles, Google on algorithmic rigor. Nine styles, each changing the room.",
  },
  {
    icon: Mic,
    title: "Voice mode",
    body: "Speak your answers instead of typing, so you practise the way the real thing actually feels.",
  },
  {
    icon: Gauge,
    title: "A readiness verdict",
    body: "Finish with a percentage, the gaps that cost you, and a week-by-week plan to close them.",
  },
];

const FLOW = ["Question", "Answer", "Evaluation", "Follow-up", "Hint", "Next"];

export default function LandingPage() {
  const token = useAuthStore((s) => s.token);
  const refresh = useAuthStore((s) => s.refresh);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <main className="flex flex-1 flex-col">
      {/* ------------------------------------------------------------- nav */}
      <header className="sticky top-0 z-40 border-b border-line-subtle bg-canvas/70 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-3.5">
          <span className="text-[0.9375rem] font-semibold tracking-tight">
            Interview<span className="text-accent-bright">Pilot</span>
          </span>
          <div className="flex items-center gap-2">
            {token ? (
              <Link href="/dashboard">
                <Button size="sm">Dashboard</Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button size="sm" variant="ghost">
                    Sign in
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">Get started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ----------------------------------------------------------- hero */}
      <section className="relative overflow-hidden">
        <div className="grid-backdrop pointer-events-none absolute inset-0" aria-hidden />

        <div className="relative mx-auto w-full max-w-6xl px-6 pt-20 pb-16 text-center">
          <div className="animate-fade-up">
            <Badge tone="accent" className="mb-6">
              <Sparkles className="h-3 w-3" />
              Powered by GPT-5 structured outputs
            </Badge>

            <h1 className="mx-auto max-w-3xl text-balance text-5xl leading-[1.05] font-semibold tracking-tight sm:text-6xl">
              Mock interviews that
              <br />
              <span className="text-gradient">actually push back</span>
            </h1>

            <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-ink-secondary">
              Most practice tools read you a list of questions. InterviewPilot reads your resume,
              runs a real adaptive interview, scores every answer, and tells you exactly how ready
              you are.
            </p>

            <div className="mt-9 flex flex-wrap justify-center gap-3">
              <Link href={token ? "/dashboard" : "/register"}>
                <Button size="lg">
                  {token ? "Go to dashboard" : "Start practising free"}
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href={token ? "/interview/new" : "/login"}>
                <Button size="lg" variant="outline">
                  {token ? "New interview" : "Sign in"}
                </Button>
              </Link>
            </div>
          </div>

          {/* ------------------------------------------- the loop, visualised */}
          <div className="animate-fade-up mt-14" style={{ animationDelay: "0.12s" }}>
            <p className="text-[0.6875rem] tracking-[0.18em] text-ink-faint uppercase">
              The loop is not question → answer → question
            </p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-x-1.5 gap-y-2">
              {FLOW.map((step, index) => (
                <div key={step} className="flex items-center gap-1.5">
                  <span
                    className={
                      index >= 2
                        ? "rounded-full border border-accent-line bg-accent-dim px-3 py-1 text-xs font-medium text-accent-bright"
                        : "rounded-full border border-line bg-surface-2 px-3 py-1 text-xs text-ink-secondary"
                    }
                  >
                    {step}
                  </span>
                  {index < FLOW.length - 1 && <ArrowRight className="h-3 w-3 text-ink-faint" />}
                </div>
              ))}
            </div>
          </div>

          {/* ------------------------------------------------ product preview */}
          <div
            className="animate-fade-up surface-edge-lg mx-auto mt-14 max-w-3xl overflow-hidden rounded-xl border border-line bg-surface-1 text-left"
            style={{ animationDelay: "0.22s" }}
          >
            <div className="flex items-center gap-2 border-b border-line-subtle bg-surface-2/60 px-4 py-2.5">
              <span className="h-2.5 w-2.5 rounded-full bg-bad/60" />
              <span className="h-2.5 w-2.5 rounded-full bg-warn/60" />
              <span className="h-2.5 w-2.5 rounded-full bg-good/60" />
              <span className="ml-2 text-xs text-ink-faint">
                Backend Engineer · Amazon style · question 2 of 6
              </span>
              <span className="live-dot ml-auto h-1.5 w-1.5 rounded-full bg-good" />
            </div>

            <div className="space-y-3 p-5">
              <Bubble side="left">
                Walk me through a time you had to make a call without complete data. What did you
                decide, and what did it cost?
              </Bubble>
              <Bubble side="right">
                We were seeing intermittent 5xx spikes and only had partial tracing…
              </Bubble>

              <div className="ml-auto max-w-[86%] rounded-md border border-line-subtle bg-surface-2/70 p-3">
                <div className="flex items-center gap-3 text-xs">
                  <span className="tabular font-semibold text-good">84/100</span>
                  <span className="text-ink-faint">
                    Technical 82 · Communication 88 · Clarity 85
                  </span>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-ink-secondary">
                  Strong STAR structure and a real trade-off. Quantify the blast radius next time.
                </p>
              </div>

              <Bubble side="left" kind="Follow-up">
                You mentioned rolling back — how would you have detected it sooner?
              </Bubble>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------- features */}
      <section className="mx-auto w-full max-w-6xl px-6 py-20">
        <h2 className="text-center text-3xl font-semibold tracking-tight">
          Built like the real thing
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-center text-ink-secondary">
          Every part of a real loop — the resume read, the probing, the scoring, the debrief.
        </p>

        <div className="stagger mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="surface-edge rounded-lg border border-line-subtle bg-surface-1/70 p-5 transition-colors duration-200 hover:border-line hover:bg-surface-2/70"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent-dim">
                <feature.icon className="h-4.5 w-4.5 text-accent-bright" />
              </div>
              <h3 className="mt-4 font-medium">{feature.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-secondary">{feature.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------------ CTA */}
      <section className="mx-auto w-full max-w-6xl px-6 pb-24">
        <div className="surface-edge-lg relative overflow-hidden rounded-xl border border-accent-line bg-gradient-to-br from-accent-dim to-transparent px-8 py-14 text-center">
          <h2 className="text-3xl font-semibold tracking-tight">Find out where you actually are</h2>
          <p className="mx-auto mt-3 max-w-md text-ink-secondary">
            One interview gives you six scores, your weak topics, and a plan. It takes about ten
            minutes.
          </p>
          <Link href={token ? "/interview/new" : "/register"} className="mt-8 inline-block">
            <Button size="lg">
              {token ? "Start an interview" : "Create your account"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      <footer className="border-t border-line-subtle py-8">
        <p className="text-center text-xs text-ink-faint">
          InterviewPilot AI — practice guidance, not a hiring decision.
        </p>
      </footer>
    </main>
  );
}

function Bubble({
  side,
  kind,
  children,
}: {
  side: "left" | "right";
  kind?: string;
  children: React.ReactNode;
}) {
  const isLeft = side === "left";
  return (
    <div className={isLeft ? "flex justify-start" : "flex justify-end"}>
      <div
        className={
          isLeft
            ? "max-w-[86%] rounded-md rounded-bl-sm bg-surface-3 px-3.5 py-2.5 text-sm leading-relaxed text-ink"
            : "max-w-[86%] rounded-md rounded-br-sm bg-accent/85 px-3.5 py-2.5 text-sm leading-relaxed text-white"
        }
      >
        {kind && (
          <span className="mb-1 block text-[0.6875rem] font-medium text-accent-bright">{kind}</span>
        )}
        {children}
      </div>
    </div>
  );
}
