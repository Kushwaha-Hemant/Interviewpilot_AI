"use client";

import { Check } from "lucide-react";
import Link from "next/link";

/**
 * Split auth shell: form on the left, proof on the right.
 *
 * The right panel is hidden below lg — on a phone it would push the form below the
 * fold, and the form is the only thing that matters there.
 */
export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <main className="flex min-h-full flex-1">
      {/* ---------------------------------------------------------- form */}
      <div className="flex flex-1 flex-col px-6 py-8">
        <Link href="/" className="text-[0.9375rem] font-semibold tracking-tight">
          Interview<span className="text-accent-bright">Pilot</span>
        </Link>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="animate-fade-up w-full max-w-sm">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-1.5 text-sm text-ink-secondary">{subtitle}</p>

            <div className="mt-8">{children}</div>

            <div className="mt-6 text-center text-sm text-ink-secondary">{footer}</div>
          </div>
        </div>

        <p className="text-center text-xs text-ink-faint lg:text-left">
          Practice guidance, not a hiring decision.
        </p>
      </div>

      {/* --------------------------------------------------------- proof */}
      <aside className="relative hidden w-[46%] max-w-2xl overflow-hidden border-l border-line-subtle bg-surface-1 lg:block">
        <div className="grid-backdrop pointer-events-none absolute inset-0" aria-hidden />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(38rem 26rem at 70% 8%, rgba(99,102,241,0.16), transparent 62%)",
          }}
          aria-hidden
        />

        <div className="relative flex h-full flex-col justify-center px-14">
          <blockquote className="text-2xl leading-snug font-medium text-balance">
            “Most tools read you questions. This one listens to the answer and asks the thing a
            real interviewer would ask next.”
          </blockquote>

          <ul className="mt-10 space-y-3.5">
            {[
              "Questions generated from your resume and the job spec",
              "Follow-ups and hints driven by how you actually answered",
              "Six scores per answer, stored and trended over time",
              "A readiness percentage and a week-by-week plan",
            ].map((line) => (
              <li key={line} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-good-dim">
                  <Check className="h-3 w-3 text-good" />
                </span>
                <span className="text-sm text-ink-secondary">{line}</span>
              </li>
            ))}
          </ul>

          <div className="mt-12 flex items-center gap-6 border-t border-line-subtle pt-8">
            <Stat value="6" label="Score dimensions" />
            <Stat value="9" label="Company styles" />
            <Stat value="4" label="Interview modes" />
          </div>
        </div>
      </aside>
    </main>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="tabular text-2xl font-semibold">{value}</p>
      <p className="mt-0.5 text-xs text-ink-tertiary">{label}</p>
    </div>
  );
}
