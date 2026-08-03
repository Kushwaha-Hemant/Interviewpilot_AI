"use client";

import type { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";

/** A headline number needs no plot — value, label, and one line of context. */
export function StatTile({
  label,
  value,
  hint,
  icon: Icon,
  valueClassName,
  accessory,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: LucideIcon;
  valueClassName?: string;
  accessory?: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[0.8125rem] text-ink-secondary">{label}</p>
        {Icon && <Icon className="h-4 w-4 shrink-0 text-ink-faint" />}
      </div>

      <div className="mt-2.5 flex items-baseline gap-2">
        <p className={cn("tabular text-[2rem] leading-none font-semibold", valueClassName)}>
          {value}
        </p>
        {accessory}
      </div>

      {hint && <p className="mt-2 text-xs text-ink-tertiary">{hint}</p>}
    </Card>
  );
}
