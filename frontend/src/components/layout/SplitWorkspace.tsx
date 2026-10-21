import { type ReactNode, useState } from "react";

import { usePrefers } from "../../lib/usePrefers";

interface SplitWorkspaceProps {
  left: ReactNode;
  right: ReactNode;
  /** Viewport width (px) below which the panes stack behind a segmented control. */
  narrowBreakpointPx: number;
}

type Pane = "overview" | "copilot";
const PANES: { id: Pane; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "copilot", label: "Copilot" },
];

function Segments({ pane, onChange }: { pane: Pane; onChange: (pane: Pane) => void }) {
  return (
    <div role="tablist" aria-label="Pane" className="glass m-2 grid grid-cols-2 gap-1 rounded-xl p-1">
      {PANES.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={pane === id}
          onClick={() => onChange(id)}
          className={`spring rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-300 ${
            pane === id ? "bg-accent text-accent-fg" : "text-fg2"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

/**
 * The locked full-viewport shell: overview on the left (64%), copilot on the right (36%).
 * On a narrow viewport one pane shows at a time (both stay mounted, so nothing is lost).
 */
export function SplitWorkspace({ left, right, narrowBreakpointPx }: SplitWorkspaceProps) {
  const narrow = usePrefers(`(max-width: ${narrowBreakpointPx - 1}px)`);
  const [pane, setPane] = useState<Pane>("overview");
  const hide = (id: Pane) => (narrow && pane !== id ? "hidden" : "");
  return (
    <div
      className={`grid h-dvh w-dvw overflow-hidden ${
        narrow ? "grid-cols-1 grid-rows-[auto_minmax(0,1fr)]" : "grid-cols-[64fr_36fr]"
      }`}
    >
      {narrow && <Segments pane={pane} onChange={setPane} />}
      <section aria-label="Overview" className={`min-h-0 min-w-0 overflow-hidden ${hide("overview")}`}>
        {left}
      </section>
      <section
        aria-label="Copilot"
        className={`min-h-0 min-w-0 overflow-hidden ${narrow ? "" : "border-l border-hairline"} ${hide("copilot")}`}
      >
        {right}
      </section>
    </div>
  );
}
