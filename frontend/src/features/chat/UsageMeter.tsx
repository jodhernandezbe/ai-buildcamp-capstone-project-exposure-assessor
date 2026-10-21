import { Coins } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import type { Usage, UsageTotals } from "../../types/workspace";
import { formatCost, formatExact, formatTokens, totalTokens } from "./formatUsage";

function Row({ label, totals }: { label: string; totals: UsageTotals }) {
  return (
    <section aria-label={label} className="py-2">
      <h3 className="mb-1 text-xs font-medium text-fg2">{label}</h3>
      <dl className="grid grid-cols-[1fr_auto] gap-x-6 gap-y-0.5 text-sm">
        <dt>Model calls</dt>
        <dd>{formatExact(totals.calls)}</dd>
        <dt>Input tokens</dt>
        <dd>{formatExact(totals.input_tokens)}</dd>
        <dt>Cached input</dt>
        <dd>{formatExact(totals.cached_input_tokens)}</dd>
        <dt>Output tokens</dt>
        <dd>{formatExact(totals.output_tokens)}</dd>
        <dt>Cost</dt>
        <dd>{formatCost(totals)}</dd>
      </dl>
    </section>
  );
}

function notes(usage: Usage): string[] {
  const { session } = usage;
  const lines: string[] = [];
  if (!session.complete) lines.push("Some calls reported no usage, so these totals are a minimum.");
  if (session.cost_status === "unpriced") lines.push("No price is configured for this model.");
  else lines.push(`Estimated from list prices${session.priced_on ? ` (priced ${session.priced_on})` : ""}.`);
  return lines;
}

/** Session tokens and estimated cost in the header, with a breakdown popover. */
export function UsageMeter({ usage }: { usage: Usage | null }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onPointer = (event: MouseEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
    };
  }, [open]);

  if (!usage) return null;
  const { session } = usage;
  return (
    <div ref={root} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`Usage: ${formatTokens(totalTokens(session))} tokens, ${formatCost(session)}`}
        onClick={() => setOpen((value) => !value)}
        className="spring flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs text-fg2 transition hover:bg-hairline hover:text-fg"
      >
        <Coins size={14} aria-hidden="true" />
        <span>{formatTokens(totalTokens(session))} tokens</span>
        <span aria-hidden="true">·</span>
        <span>{formatCost(session)}</span>
      </button>
      {open ? (
        <div
          id={panelId}
          role="region"
          aria-label="Usage breakdown"
          className="glass sheet-in absolute right-0 top-full z-40 mt-2 w-72 rounded-2xl p-4 shadow-[var(--shadow)]"
        >
          <Row label="Last turn" totals={usage.turn} />
          <hr className="border-hairline" />
          <Row label="Session" totals={session} />
          {notes(usage).map((line) => (
            <p key={line} className="mt-2 text-xs text-fg2">
              {line}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}
