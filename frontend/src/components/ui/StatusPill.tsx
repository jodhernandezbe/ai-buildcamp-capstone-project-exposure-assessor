import type { Status } from "../../types/workspace";

const LOOK: Record<Status, { label: string; tone: string }> = {
  below: { label: "Below concern", tone: "bg-ok/15 text-ok" },
  near: { label: "Near concern", tone: "bg-warn/15 text-warn" },
  above: { label: "Above concern", tone: "bg-bad/15 text-bad" },
};

/** Risk status as a coloured pill that also says it in words (colour is never the only cue). */
export function StatusPill({ status }: { status: Status | null }) {
  const { label, tone } = status
    ? LOOK[status]
    : { label: "Not computed", tone: "bg-fg2/10 text-fg2" };
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${tone}`}
      data-status={status ?? "none"}
    >
      {label}
    </span>
  );
}
