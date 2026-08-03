"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { AuthLayout } from "@/components/AuthLayout";
import { Button, ErrorMessage, Field, Input } from "@/components/ui/primitives";
import { ApiError, EMAIL_NOT_VERIFIED } from "@/services/api";
import { useAuthStore } from "@/store/auth";

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>();

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      await login(values.email, values.password);
      router.replace("/dashboard");
    } catch (error) {
      // Credentials were right but the address was never confirmed — the backend has
      // already sent a fresh code, so send them straight to the verify screen.
      if (error instanceof ApiError && error.detailCode === EMAIL_NOT_VERIFIED) {
        router.replace(`/verify?email=${encodeURIComponent(values.email)}`);
        return;
      }
      setServerError(error instanceof Error ? error.message : "Sign in failed");
    }
  });

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to pick up where you left off."
      footer={
        <>
          No account?{" "}
          <Link href="/register" className="text-accent-bright hover:underline">
            Create one
          </Link>
        </>
      }
    >
      {/* method="post" matters: if JS fails to hydrate, the browser would otherwise fall
          back to a native GET submit and put the password in the URL and history. */}
      <form method="post" onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            aria-invalid={!!errors.email}
            {...register("email", { required: "Email is required" })}
          />
        </Field>

        <Field label="Password" htmlFor="password" error={errors.password?.message}>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            aria-invalid={!!errors.password}
            {...register("password", { required: "Password is required" })}
          />
        </Field>

        <ErrorMessage>{serverError}</ErrorMessage>

        <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthLayout>
  );
}
