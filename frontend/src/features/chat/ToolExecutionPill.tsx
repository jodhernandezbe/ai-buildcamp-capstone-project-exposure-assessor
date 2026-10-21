import { AlertCircle, Check, ChevronRight, LoaderCircle } from "lucide-react";
import { useId, useState } from "react";

import type { ToolStep } from "../../hooks/chatState";

const ICON = {
  running: <LoaderCircle size={13} aria-hidden="true" className="animate-spin text-fg2" />,
  done: <Check size={13} aria-hidden="true" className="text-ok" />,
  error: <AlertCircle size={13} aria-hidden="true" className="text-bad" />,
} as const;

const STATE_LABEL = { running: "running", done: "done", error: "failed" } as const;

/** One tool step: its label and whether it is running, done or failed. */
function Pill({ step }: { step: ToolStep }) {
  return (
    <li
      className="glass inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs text-fg2"
      aria-label={`${step.label}, ${STATE_LABEL[step.state]}`}
    >
      {ICON[step.state]}
      {step.label}
    </li>
  );
}

/** A turn's tool steps as compact pills in one row; click to expand them all. */
export function ToolExecutionPills({ steps }: { steps: ToolStep[] }) {
  const [expanded, setExpanded] = useState(false);
  const listId = useId();
  if (steps.length === 0) return null;
  const running = steps.filter((step) => step.state === "running").length;
  const summary = running > 0 ? `Working… ${running} running` : `${steps.length} steps`;

  return (
    <div className="mb-2">
      <button
        type="button"
        aria-expanded={expanded}
        aria-controls={listId}
        onClick={() => setExpanded((value) => !value)}
        className="spring mb-1 flex items-center gap-1 text-xs text-fg2 transition hover:text-fg"
      >
        <ChevronRight
          size={13}
          aria-hidden="true"
          className={`transition-transform ${expanded ? "rotate-90" : ""}`}
        />
        {summary}
      </button>
      <ul
        id={listId}
        className={`flex gap-1.5 ${expanded ? "flex-wrap" : "flex-nowrap overflow-hidden"}`}
      >
        {steps.map((step) => (
          <Pill key={step.callId} step={step} />
        ))}
      </ul>
    </div>
  );
}
