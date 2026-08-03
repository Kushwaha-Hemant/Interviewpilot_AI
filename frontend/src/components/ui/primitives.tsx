"use client";

/**
 * Core UI primitives.
 *
 * shadcn/ui-compatible surface area (variant/size props, `cn` merging) but written by
 * hand against this project's design tokens, so there is no generator coupling and every
 * component speaks in surface/line/ink terms rather than raw palette values.
 */

import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

// ------------------------------------------------------------------------ Button

const buttonVariants = cva(
  "relative inline-flex items-center justify-center gap-2 font-medium whitespace-nowrap transition-all duration-150 ease-[cubic-bezier(0.22,1,0.36,1)] select-none disabled:pointer-events-none disabled:opacity-45 active:scale-[0.985]",
  {
    variants: {
      variant: {
        // Inset highlight + shadow gives the primary button physical weight.
        primary:
          "bg-accent text-white shadow-[inset_0_1px_0_0_rgba(255,255,255,0.16),0_1px_2px_rgba(0,0,0,0.4)] hover:bg-accent-bright hover:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.2),0_4px_14px_-4px_rgba(99,102,241,0.6)]",
        secondary:
          "bg-surface-3 text-ink shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] hover:bg-surface-hover",
        outline:
          "border border-line text-ink-secondary hover:border-line-strong hover:text-ink hover:bg-surface-2",
        ghost: "text-ink-secondary hover:bg-surface-2 hover:text-ink",
        danger: "bg-bad text-white hover:brightness-110",
        link: "text-accent-bright underline-offset-4 hover:underline",
      },
      size: {
        xs: "h-7 rounded-[--radius-xs] px-2.5 text-xs",
        sm: "h-8 rounded-sm px-3 text-[0.8125rem]",
        md: "h-10 rounded-md px-4 text-sm",
        lg: "h-12 rounded-md px-6 text-[0.9375rem]",
        icon: "h-10 w-10 rounded-md",
        "icon-sm": "h-8 w-8 rounded-sm",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    >
      {loading && <Spinner className="h-3.5 w-3.5" />}
      {children}
    </button>
  ),
);
Button.displayName = "Button";

// -------------------------------------------------------------------------- Card

export function Card({
  className,
  interactive,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { interactive?: boolean }) {
  return (
    <div
      className={cn(
        "surface-edge rounded-lg border border-line-subtle bg-surface-1/80 backdrop-blur-xl",
        interactive &&
          "transition-colors duration-200 hover:border-line hover:bg-surface-2/80",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-center gap-2 px-5 pt-5", className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-[0.8125rem] font-medium tracking-wide text-ink-secondary uppercase",
        className,
      )}
      {...props}
    />
  );
}

export function CardBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5", className)} {...props} />;
}

// ------------------------------------------------------------------------- Fields

export function Field({
  label,
  hint,
  error,
  htmlFor,
  children,
  className,
}: {
  label: string;
  hint?: string;
  error?: string;
  htmlFor?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={htmlFor} className="text-[0.8125rem] font-medium text-ink-secondary">
          {label}
        </label>
        {hint && <span className="text-xs text-ink-faint">{hint}</span>}
      </div>
      {children}
      {error && (
        <p role="alert" className="text-xs text-bad">
          {error}
        </p>
      )}
    </div>
  );
}

const fieldBase =
  "w-full rounded-sm border border-line bg-surface-2/60 text-ink placeholder:text-ink-faint transition-colors duration-150 focus:border-accent focus:bg-surface-2 focus:outline-none focus:ring-2 focus:ring-accent/25 disabled:opacity-50";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={cn(fieldBase, "h-10 px-3 text-sm", className)} {...props} />
  ),
);
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(fieldBase, "resize-none p-3 text-sm leading-relaxed", className)}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      fieldBase,
      "h-10 cursor-pointer appearance-none bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22%236e6e7c%22 stroke-width=%222%22><path d=%22M6 9l6 6 6-6%22/></svg>')] bg-[length:1rem] bg-[right_0.6rem_center] bg-no-repeat py-0 pr-9 pl-3 text-sm",
      className,
    )}
    {...props}
  />
));
Select.displayName = "Select";

// ------------------------------------------------------------------------- Badge

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
  {
    variants: {
      tone: {
        default: "bg-surface-3 text-ink-secondary",
        accent: "bg-accent-dim text-accent-bright",
        good: "bg-good-dim text-good",
        warn: "bg-warn-dim text-warn",
        bad: "bg-bad-dim text-bad",
        info: "bg-info-dim text-info",
        outline: "border border-line text-ink-secondary",
      },
    },
    defaultVariants: { tone: "default" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

// ---------------------------------------------------------------------- Feedback

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        "inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current/25 border-t-current",
        className,
      )}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("skeleton", className)} />;
}

export function ErrorMessage({ children }: { children?: React.ReactNode }) {
  if (!children) return null;
  return (
    <p
      role="alert"
      className="flex items-start gap-2 rounded-sm border border-bad/25 bg-bad-dim px-3 py-2 text-sm text-bad"
    >
      {children}
    </p>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  body,
  action,
  className,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  body?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-md border border-dashed border-line px-6 py-10 text-center",
        className,
      )}
    >
      {Icon && (
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-surface-2">
          <Icon className="h-5 w-5 text-ink-tertiary" />
        </div>
      )}
      <p className="text-sm font-medium text-ink">{title}</p>
      {body && <p className="mt-1 max-w-xs text-xs leading-relaxed text-ink-tertiary">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** Meter bar. `tone` is derived from the score band by the caller. */
export function Meter({
  value,
  tone = "var(--color-accent)",
  className,
}: {
  value: number;
  tone?: string;
  className?: string;
}) {
  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-surface-3", className)}>
      <div
        className="h-full rounded-full transition-[width] duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
        style={{ width: `${Math.max(Math.min(value, 100), 0)}%`, background: tone }}
      />
    </div>
  );
}

/** Lightweight CSS tooltip — no portal, no dependency, keyboard reachable. */
export function Tooltip({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <span className="group/tip relative inline-flex">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 scale-95 rounded-sm border border-line bg-surface-3 px-2 py-1 text-xs whitespace-nowrap text-ink opacity-0 shadow-lg transition-all duration-150 group-hover/tip:scale-100 group-hover/tip:opacity-100 group-focus-within/tip:scale-100 group-focus-within/tip:opacity-100"
      >
        {label}
      </span>
    </span>
  );
}
