import { formatOutcome } from "./format";

const TONE = {
  ok: "bg-ok/15 text-ok",
  error: "bg-bad/15 text-bad",
  unknown: "bg-fg2/10 text-fg2",
} as const;

/** A run's or call's outcome as a coloured pill that also says it in words. */
export function OutcomePill({ outcome }: { outcome: keyof typeof TONE }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${TONE[outcome]}`}
    >
      {formatOutcome(outcome)}
    </span>
  );
}
