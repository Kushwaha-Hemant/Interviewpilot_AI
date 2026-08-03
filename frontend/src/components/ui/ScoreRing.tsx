"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";
import { scoreToken } from "@/lib/score";

/**
 * Circular score gauge.
 *
 * The arc sweeps from 0 on mount so the number lands rather than appears — the one
 * place in the product where a little ceremony is warranted, because this is the
 * single number the candidate came for.
 */
export function ScoreRing({
  value,
  size = 132,
  stroke = 9,
  label,
  suffix = "",
  className,
}: {
  value: number | null;
  size?: number;
  stroke?: number;
  label?: string;
  suffix?: string;
  className?: string;
}) {
  const target = value ?? 0;
  const [shown, setShown] = useState(0);

  useEffect(() => {
    // Next frame, so the transition has a 0 -> target change to animate.
    const id = requestAnimationFrame(() => setShown(target));
    return () => cancelAnimationFrame(id);
  }, [target]);

  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - shown / 100);
  const color = scoreToken(value);

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-surface-3)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: "stroke-dashoffset 1.1s cubic-bezier(0.22, 1, 0.36, 1)",
            filter: `drop-shadow(0 0 10px ${color}55)`,
          }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="tabular text-3xl leading-none font-semibold"
          style={{ color }}
          role="img"
          aria-label={`${label ?? "Score"}: ${value ?? "not available"}`}
        >
          {value == null ? "—" : Math.round(value)}
          {value != null && suffix && <span className="text-lg">{suffix}</span>}
        </span>
        {label && (
          <span className="mt-1 text-[0.6875rem] tracking-wide text-ink-tertiary uppercase">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
