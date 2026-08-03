"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { AuthLayout } from "@/components/AuthLayout";
import { Button, ErrorMessage, Field, Input } from "@/components/ui/primitives";
import { useAuthStore } from "@/store/auth";
import { needsVerification } from "@/types";

interface RegisterForm {
  fullName: string;
  email: string;
  password: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const registerUser = useAuthStore((s) => s.register);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>();

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      const result = await registerUser(values.email, values.password, values.fullName);
      if (needsVerification(result)) {
        const query = new URLSearchParams({ email: result.email, delivery: result.delivery });
        router.replace(`/verify?${query}`);
      } else {
        router.replace("/dashboard");
      }
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Sign up failed");
    }
  });

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Free, and your first interview takes about ten minutes."
      footer={
        <>
          Already registered?{" "}
          <Link href="/login" className="text-accent-bright hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      {/* method="post" matters: if JS fails to hydrate, the browser would otherwise fall
          back to a native GET submit and put the password in the URL and history. */}
      <form method="post" onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Name" htmlFor="fullName" hint="Optional">
          <Input id="fullName" autoComplete="name" placeholder="Alex Candidate" {...register("fullName")} />
        </Field>

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

        <Field
          label="Password"
          htmlFor="password"
          hint="8+ characters"
          error={errors.password?.message}
        >
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            aria-invalid={!!errors.password}
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Use at least 8 characters" },
            })}
          />
        </Field>

        <ErrorMessage>{serverError}</ErrorMessage>

        <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthLayout>
  );
}
