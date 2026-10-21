import type { UsageTotals } from "../../types/workspace";

const COMPACT = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const WHOLE = new Intl.NumberFormat("en-US");

/** Token count for the pill: 12,345 -> "12.3K". */
export const formatTokens = (count: number): string => COMPACT.format(count);

/** Exact token count for the breakdown: 12345 -> "12,345". */
export const formatExact = (count: number): string => WHOLE.format(count);

/** Dollars: four decimals under $1 (a turn costs cents), two from $1 up: "$0.0123", "$1.24". */
export function formatUsd(usd: number): string {
  return `$${usd.toFixed(usd < 1 ? 4 : 2)}`;
}

/** The cost as the server qualified it: estimate, lower bound or unpriced. */
export function formatCost(totals: UsageTotals): string {
  if (totals.cost_usd === null || totals.cost_status === "unpriced") return "unpriced";
  const amount = formatUsd(totals.cost_usd);
  return totals.cost_status === "lower_bound" ? `≥ ${amount}` : `~${amount}`;
}

/** All tokens the provider reported for these calls (input and output). */
export const totalTokens = (totals: UsageTotals): number =>
  totals.input_tokens + totals.output_tokens;
