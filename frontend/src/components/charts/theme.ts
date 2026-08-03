/**
 * Chart tokens.
 *
 * The two series hexes are the dark-mode steps of the reference categorical palette,
 * re-validated as a pair against this app's chart surface (#14141d): lightness band,
 * chroma floor, CVD separation (worst adjacent ΔE 26.8 protan), normal-vision
 * separation (ΔE 31.8) and ≥3:1 contrast all pass.
 *
 * Re-run scripts/validate_palette.js before adding a third series or changing a hue.
 * Chrome is mapped onto the app's own surface/line/ink tokens so charts sit inside the
 * same cards as everything else.
 */

export const CHART = {
  surface: "#14141d",
  series1: "#3987e5", // overall score, radar
  series2: "#d95926", // confidence
  grid: "rgba(255,255,255,0.06)",
  axis: "rgba(255,255,255,0.12)",
  muted: "#6e6e7c",
  ink: "#f4f4f6",
} as const;

/** Shared Recharts tooltip styling — one definition so every chart matches. */
export const tooltipStyle = {
  contentStyle: {
    background: "#1c1c27",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "0.5rem",
    fontSize: "0.75rem",
    padding: "0.5rem 0.65rem",
    color: CHART.ink,
    boxShadow: "0 12px 32px -12px rgba(0,0,0,0.8)",
  },
  labelStyle: { color: CHART.muted, marginBottom: 4, fontSize: "0.6875rem" },
  itemStyle: { color: CHART.ink, padding: 0 },
  cursor: { stroke: CHART.axis, strokeWidth: 1 },
} as const;
