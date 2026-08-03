"use client";

import { MailCheck, Terminal } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { AuthLayout } from "@/components/AuthLayout";
import { Button, ErrorMessage, Spinner } from "@/components/ui/primitives";
import { OtpInput } from "@/components/ui/OtpInput";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";

export default function VerifyPage() {
  // useSearchParams needs a Suspense boundary in the App Router.
  return (
    <Suspense
      fallback={
        <main className="flex flex-1 items-center justify-center">
          <Spinner className="h-6 w-6" />
        </main>
      }
    >
      <VerifyContent />
    </Suspense>
  );
}

function VerifyContent() {
  const router = useRouter();
  const params = useSearchParams();
  const verifyEmail = useAuthStore((s) => s.verifyEmail);

  const email = params.get("email") ?? "";
  const consoleDelivery = params.get("delivery") === "console";

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(60);

  // No email in the URL means the user landed here directly — send them back.
  useEffect(() => {
    if (!email) router.replace("/register");
  }, [email, router]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = window.setInterval(() => setCooldown((s) => Math.max(0, s - 1)), 1000);
    return () => window.clearInterval(id);
  }, [cooldown]);

  const submit = useCallback(
    async (value: string) => {
      if (value.length !== 6 || submitting) return;
      setSubmitting(true);
      setError(null);
      setNotice(null);
      try {
        await verifyEmail(email, value);
        router.replace("/dashboard");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Verification failed");
        setCode("");
        setSubmitting(false);
      }
    },
    [email, submitting, verifyEmail, router],
  );

  async function resend() {
    setError(null);
    setNotice(null);
    try {
      await api.resendCode(email);
      setNotice("A new code is on its way.");
      setCode("");
      setCooldown(60);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resend the code");
    }
  }

  if (!email) return null;

  return (
    <AuthLayout
      title="Check your email"
      subtitle={`We sent a 6-digit code to ${email}. It expires in 10 minutes.`}
      footer={
        <>
          Wrong address?{" "}
          <Link href="/register" className="text-accent-bright hover:underline">
            Start over
          </Link>
        </>
      }
    >
      <div className="space-y-5">
        {/* Without a mail server the code goes to the backend log — say so plainly
            rather than letting someone wait for an email that will never arrive. */}
        {consoleDelivery && (
          <div className="flex gap-3 rounded-sm border border-warn/25 bg-warn-dim p-3">
            <Terminal className="mt-0.5 h-4 w-4 shrink-0 text-warn" />
            <div className="text-xs leading-relaxed text-ink-secondary">
              <p className="font-medium text-warn">No mail server configured</p>
              <p className="mt-0.5">
                Your code was printed in the backend terminal instead. Set{" "}
                <code className="rounded-[3px] bg-surface-3 px-1">SMTP_HOST</code> in{" "}
                <code className="rounded-[3px] bg-surface-3 px-1">backend/.env</code> to send
                real email.
              </p>
            </div>
          </div>
        )}

        <OtpInput
          value={code}
          onChange={setCode}
          onComplete={submit}
          disabled={submitting}
          invalid={!!error}
          autoFocus
        />

        <ErrorMessage>{error}</ErrorMessage>
        {notice && (
          <p className="flex items-center gap-2 text-sm text-good">
            <MailCheck className="h-4 w-4" />
            {notice}
          </p>
        )}

        <Button
          size="lg"
          className="w-full"
          onClick={() => submit(code)}
          loading={submitting}
          disabled={code.length !== 6}
        >
          {submitting ? "Verifying…" : "Verify and continue"}
        </Button>

        <div className="text-center text-sm text-ink-tertiary">
          Didn&apos;t get it?{" "}
          {cooldown > 0 ? (
            <span className="tabular text-ink-faint">Resend in {cooldown}s</span>
          ) : (
            <button
              type="button"
              onClick={resend}
              className="text-accent-bright hover:underline"
            >
              Resend code
            </button>
          )}
        </div>
      </div>
    </AuthLayout>
  );
}
