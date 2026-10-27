import { Cpu, ExternalLink, Wrench } from "lucide-react";

import type { SessionStep, SessionTurn } from "../../types/workspace";
import { NOT_REPORTED, formatDuration, formatStarted, formatTokens } from "./format";
import { OutcomePill } from "./OutcomePill";

const PERCENT = 100;

/** The span (ms) the bars of a turn are drawn against: its own duration, or its last call's end. */
function extent(turn: SessionTurn): number {
  const ends = turn.steps.map((step) => step.offset_ms + (step.duration_ms ?? 0));
  return Math.max(turn.duration_ms ?? 0, ...ends);
}

/** Where a call sits in its turn, as shares of the turn's span; a call without a duration has no bar. */
function bar(step: SessionStep, total: number): { left: string; width: string } | null {
  if (total <= 0 || step.duration_ms === null) return null;
  return {
    left: `${(step.offset_ms / total) * PERCENT}%`,
    width: `${Math.max((step.duration_ms / total) * PERCENT, 1)}%`,
  };
}

function Step({ step, total }: { step: SessionStep; total: number }) {
  const Icon = step.kind === "model" ? Cpu : Wrench;
  const shape = bar(step, total);
  return (
    <li className="grid grid-cols-[minmax(0,14rem)_minmax(6rem,1fr)_auto] items-center gap-3 py-1.5 text-sm">
      <span className="flex min-w-0 items-center gap-2">
        <Icon size={15} aria-hidden="true" className="shrink-0 text-fg2" />
        <span className="min-w-0 truncate" title={step.name}>
          <span className="sr-only">{step.kind === "model" ? "Model call: " : "Tool call: "}</span>
          {step.name}
        </span>
      </span>
      <span aria-hidden="true" className="relative h-1.5 rounded-full bg-hairline">
        {shape ? <span className="absolute inset-y-0 rounded-full bg-accent" style={shape} /> : null}
      </span>
      <span className="flex items-center justify-end gap-3 whitespace-nowrap text-xs text-fg2">
        {step.kind === "model" ? <span>{formatTokens(step.input_tokens, step.output_tokens)}</span> : null}
        <span>{formatDuration(step.duration_ms)}</span>
        {step.outcome === "ok" ? null : <OutcomePill outcome={step.outcome} />}
      </span>
    </li>
  );
}

/** One turn: when it ran, its question and outcome, a link to its trace and its calls in order. */
export function TurnTimeline({ turn, index }: { turn: SessionTurn; index: number }) {
  const total = extent(turn);
  return (
    <section aria-label={`Turn ${index + 1}`} className="rounded-2xl border border-hairline p-3">
      <header className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <h4 className="text-sm font-semibold">Turn {index + 1}</h4>
        <span className="text-xs text-fg2">{formatStarted(turn.started_at)}</span>
        <span className="text-xs text-fg2">{formatDuration(turn.duration_ms)}</span>
        <OutcomePill outcome={turn.outcome} />
        {turn.trace_url ? (
          <a
            href={turn.trace_url}
            target="_blank"
            rel="noopener noreferrer"
            className="spring ml-auto inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
          >
            Open in Logfire
            <ExternalLink size={13} aria-hidden="true" />
          </a>
        ) : null}
      </header>
      <p className="mt-1 text-sm text-fg2">{turn.question ?? NOT_REPORTED}</p>
      {turn.steps.length === 0 ? (
        <p className="mt-2 text-sm text-fg2">No model or tool calls were recorded for this turn.</p>
      ) : (
        <ol className="mt-2 divide-y divide-hairline">
          {turn.steps.map((step, position) => (
            <Step key={position} step={step} total={total} />
          ))}
        </ol>
      )}
    </section>
  );
}
