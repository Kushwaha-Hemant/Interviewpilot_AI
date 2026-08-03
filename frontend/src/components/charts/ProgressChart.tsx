"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CHART, tooltipStyle } from "@/components/charts/theme";
import { EmptyState } from "@/components/ui/primitives";
import type { TimelinePoint } from "@/types";

interface Row {
  label: string;
  overall: number | null;
  confidence: number | null;
}

/**
 * Overall score and confidence share one 0-100 axis, so they belong on one chart —
 * never a second y-scale. A soft area under each line reads the trend faster than a
 * bare stroke without adding a second encoding.
 */
export function ProgressChart({
  timeline,
  confidence,
  height = 260,
}: {
  timeline: TimelinePoint[];
  confidence: TimelinePoint[];
  height?: number;
}) {
  // A trend line through one point is noise, not information — hold the empty state
  // until there are at least two interviews to draw a direction between.
  if (timeline.length < 2) {
    return (
      <EmptyState
        title={timeline.length === 0 ? "No completed interviews yet" : "One interview so far"}
        body={
          timeline.length === 0
            ? "Finish one and your score trend starts here."
            : `You scored ${Math.round(timeline[0].score)}. Complete a second interview to see which way you're moving.`
        }
        className="h-[260px]"
      />
    );
  }

  const confidenceById = new Map(confidence.map((point) => [point.interview_id, point.score]));
  const rows: Row[] = timeline.map((point, index) => ({
    label: `#${index + 1}`,
    overall: point.score,
    confidence: confidenceById.get(point.interview_id) ?? null,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={rows} margin={{ top: 8, right: 10, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="fillOverall" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART.series1} stopOpacity={0.28} />
            <stop offset="100%" stopColor={CHART.series1} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="fillConfidence" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART.series2} stopOpacity={0.2} />
            <stop offset="100%" stopColor={CHART.series2} stopOpacity={0} />
          </linearGradient>
        </defs>

        <CartesianGrid stroke={CHART.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: CHART.muted, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: CHART.axis }}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: CHART.muted, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={46}
        />
        <Tooltip
          {...tooltipStyle}
          formatter={(value) => (typeof value === "number" ? `${Math.round(value)}/100` : "—")}
        />
        <Legend
          verticalAlign="top"
          align="right"
          height={26}
          iconType="plainline"
          iconSize={14}
          wrapperStyle={{ fontSize: "0.6875rem", color: CHART.muted }}
        />
        <Area
          type="monotone"
          name="Overall"
          dataKey="overall"
          stroke={CHART.series1}
          strokeWidth={2}
          fill="url(#fillOverall)"
          dot={{ r: 3.5, fill: CHART.series1, stroke: CHART.surface, strokeWidth: 2 }}
          activeDot={{ r: 5.5 }}
          connectNulls
        />
        <Area
          type="monotone"
          name="Confidence"
          dataKey="confidence"
          stroke={CHART.series2}
          strokeWidth={2}
          fill="url(#fillConfidence)"
          dot={{ r: 3.5, fill: CHART.series2, stroke: CHART.surface, strokeWidth: 2 }}
          activeDot={{ r: 5.5 }}
          connectNulls
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
