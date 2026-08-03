"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { CHART, tooltipStyle } from "@/components/charts/theme";
import { EmptyState } from "@/components/ui/primitives";

export interface SkillPoint {
  skill: string;
  score: number;
}

const MAX_LABEL_CHARS = 15;

/** Axis labels are drawn outside the plot; long ones run off the card, so clip them.
 *  The tooltip still shows the full skill name on hover. */
function truncate(value: string): string {
  return value.length > MAX_LABEL_CHARS ? `${value.slice(0, MAX_LABEL_CHARS - 1)}…` : value;
}

/** Single series — the card heading names it, so no legend box is needed. */
export function SkillRadar({ data, height = 280 }: { data: SkillPoint[]; height?: number }) {
  if (data.length < 3) {
    return (
      <EmptyState
        title="Not enough signal yet"
        body="Answer questions across at least three skills and your radar appears here."
        className="h-[280px]"
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart
        data={data}
        outerRadius="65%"
        margin={{ top: 12, right: 44, bottom: 12, left: 44 }}
      >
        <PolarGrid stroke={CHART.grid} />
        <PolarAngleAxis
          dataKey="skill"
          tickFormatter={truncate}
          tick={{ fill: CHART.muted, fontSize: 10 }}
          tickLine={false}
        />
        <PolarRadiusAxis
          domain={[0, 100]}
          tick={{ fill: CHART.muted, fontSize: 9 }}
          tickCount={5}
          axisLine={false}
          stroke={CHART.grid}
        />
        <Radar
          name="Score"
          dataKey="score"
          stroke={CHART.series1}
          strokeWidth={2}
          fill={CHART.series1}
          fillOpacity={0.2}
          dot={{ r: 3.5, fill: CHART.series1, stroke: CHART.surface, strokeWidth: 2 }}
          isAnimationActive
        />
        <Tooltip
          {...tooltipStyle}
          formatter={(value) => [
            typeof value === "number" ? `${Math.round(value)}/100` : "—",
            "Score",
          ]}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
