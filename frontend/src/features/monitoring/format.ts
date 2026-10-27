import type { SessionSummary } from "../../types/workspace";

/** What an absent value reads as: never 0 or a dash. */
export const NOT_REPORTED = "not reported";

const WHOLE = new Intl.NumberFormat("en-US");
const SECONDS_PER_MINUTE = 60;
const MS_PER_SECOND = 1000;

/** A count with thousands separators: 23425 -> "23,425". */
export const formatCount = (count: number | null): string =>
  count === null ? NOT_REPORTED : WHOLE.format(count);

/** Input and output tokens as "23,425 in / 88 out"; one that is absent says so. */
export function formatTokens(input: number | null, output: number | null): string {
  if (input === null && output === null) return NOT_REPORTED;
  return `${formatCount(input)} in / ${formatCount(output)} out`;
}

/** A duration from milliseconds: "420 ms", "8.7 s", "2 min 5 s". */
export function formatDuration(ms: number | null): string {
  if (ms === null) return NOT_REPORTED;
  if (ms < MS_PER_SECOND) return `${ms} ms`;
  const seconds = ms / MS_PER_SECOND;
  if (seconds < SECONDS_PER_MINUTE) return `${seconds.toFixed(1)} s`;
  const minutes = Math.floor(seconds / SECONDS_PER_MINUTE);
  return `${minutes} min ${Math.round(seconds - minutes * SECONDS_PER_MINUTE)} s`;
}

/** Dollars: four decimals under $1 (a run costs cents), two from $1 up. */
export const formatUsd = (usd: number): string => `$${usd.toFixed(usd < 1 ? 4 : 2)}`;

/** The estimated cost as the server qualified it; an absent or unknown one is not guessed. */
export function formatCost(session: Pick<SessionSummary, "cost_usd" | "cost_status">): string {
  if (session.cost_status === "unpriced") return "unpriced";
  if (session.cost_usd === null || session.cost_status === "unknown") return NOT_REPORTED;
  const amount = formatUsd(session.cost_usd);
  return session.cost_status === "lower_bound" ? `≥ ${amount}` : `~${amount}`;
}

/** A recorded time in the viewer's locale and time zone. */
export function formatStarted(iso: string): string {
  const moment = new Date(iso);
  if (Number.isNaN(moment.getTime())) return NOT_REPORTED;
  return moment.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

const OUTCOMES = {
  ok: "Completed",
  error: "Failed",
  unknown: "Unknown",
} as const;

/** An outcome in words (colour is never the only cue). */
export const formatOutcome = (outcome: keyof typeof OUTCOMES): string => OUTCOMES[outcome];
