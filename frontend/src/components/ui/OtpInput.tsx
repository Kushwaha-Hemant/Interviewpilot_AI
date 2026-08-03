"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

/**
 * Six-box one-time-code field.
 *
 * Behaviours people expect from an OTP box and notice when missing:
 *   - typing advances, Backspace on an empty box steps back
 *   - pasting the whole code fills every box (and works from one-time-code autofill)
 *   - arrow keys move between boxes
 *   - only digits are accepted, at any entry point
 *   - the value is one string in state, so the parent never reassembles fragments
 */
export function OtpInput({
  value,
  onChange,
  onComplete,
  length = 6,
  disabled,
  invalid,
  autoFocus,
}: {
  value: string;
  onChange: (value: string) => void;
  onComplete?: (value: string) => void;
  length?: number;
  disabled?: boolean;
  invalid?: boolean;
  autoFocus?: boolean;
}) {
  const refs = useRef<(HTMLInputElement | null)[]>([]);
  const completedRef = useRef<string | null>(null);

  useEffect(() => {
    if (autoFocus) refs.current[0]?.focus();
  }, [autoFocus]);

  // Fire onComplete once per distinct full value, so re-renders don't resubmit.
  useEffect(() => {
    if (value.length === length && completedRef.current !== value) {
      completedRef.current = value;
      onComplete?.(value);
    }
    if (value.length < length) completedRef.current = null;
  }, [value, length, onComplete]);

  function setDigit(index: number, digit: string) {
    const next = value.padEnd(length, " ").split("");
    next[index] = digit;
    onChange(next.join("").replace(/\s/g, "").slice(0, length));
  }

  function handleChange(index: number, raw: string) {
    const digits = raw.replace(/\D/g, "");
    if (!digits) return;

    if (digits.length > 1) {
      // Paste or autofill landed in one box — spread it across the rest.
      const merged = (value.slice(0, index) + digits).slice(0, length);
      onChange(merged);
      refs.current[Math.min(merged.length, length - 1)]?.focus();
      return;
    }

    setDigit(index, digits);
    if (index < length - 1) refs.current[index + 1]?.focus();
  }

  function handleKeyDown(index: number, event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace") {
      event.preventDefault();
      if (value[index]) {
        onChange(value.slice(0, index) + value.slice(index + 1));
      } else if (index > 0) {
        onChange(value.slice(0, index - 1) + value.slice(index));
        refs.current[index - 1]?.focus();
      }
    } else if (event.key === "ArrowLeft" && index > 0) {
      event.preventDefault();
      refs.current[index - 1]?.focus();
    } else if (event.key === "ArrowRight" && index < length - 1) {
      event.preventDefault();
      refs.current[index + 1]?.focus();
    }
  }

  return (
    <div
      className="flex justify-between gap-2"
      role="group"
      aria-label={`${length}-digit verification code`}
    >
      {Array.from({ length }).map((_, index) => (
        <input
          key={index}
          ref={(el) => {
            refs.current[index] = el;
          }}
          type="text"
          inputMode="numeric"
          // Lets iOS/Android offer the code straight from the SMS/email notification.
          autoComplete={index === 0 ? "one-time-code" : "off"}
          maxLength={length}
          disabled={disabled}
          aria-label={`Digit ${index + 1}`}
          aria-invalid={invalid}
          value={value[index] ?? ""}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={(e) => {
            e.preventDefault();
            const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
            if (pasted) {
              onChange(pasted);
              refs.current[Math.min(pasted.length, length - 1)]?.focus();
            }
          }}
          onFocus={(e) => e.currentTarget.select()}
          className={cn(
            "tabular h-14 w-full rounded-md border bg-surface-2/60 text-center text-xl font-semibold text-ink transition-colors duration-150",
            "focus:border-accent focus:bg-surface-2 focus:ring-2 focus:ring-accent/25 focus:outline-none",
            "disabled:opacity-50",
            invalid ? "border-bad" : "border-line",
          )}
        />
      ))}
    </div>
  );
}
