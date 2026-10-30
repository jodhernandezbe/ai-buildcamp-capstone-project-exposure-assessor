import type { Status } from "../../types/workspace";

const LOOK: Record<Status, { label: string; tone: string }> = {
  below: { label: "Below concern", tone: "bg-ok/15 text-ok" },
  near: { label: "Near concern", tone: "bg-warn/15 text-warn" },
  above: { label: "Above concern", tone: "bg-bad/15 text-bad" },
};

/** Risk status as a coloured pill that also says it in words (colour is never the only cue); `label` replaces the default words. */
export function StatusPill({ status, label }: { status: Status | null; label?: string }) {
  const look = status ? LOOK[status] : { label: "Not computed", tone: "bg-fg2/10 text-fg2" };
  const words = label ?? look.label;
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${look.tone}`}
      data-status={status ?? "none"}
    >
      {words}
    </span>
  );
}
