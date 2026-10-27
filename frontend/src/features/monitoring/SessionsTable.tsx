import type { SessionSummary } from "../../types/workspace";
import { NOT_REPORTED, formatCost, formatCount, formatDuration, formatStarted, formatTokens } from "./format";
import { OutcomePill } from "./OutcomePill";

const COLUMNS = [
  "Started",
  "Question",
  "Model",
  "Turns",
  "Model calls",
  "Tool calls",
  "Tokens",
  "Estimated cost",
  "Duration",
  "Status",
] as const;

interface SessionsTableProps {
  sessions: SessionSummary[];
  selectedId: string | null;
  onSelect: (sessionId: string) => void;
}

/** The recorded sessions, newest first; selecting one opens its timeline. */
export function SessionsTable({ sessions, selectedId, onSelect }: SessionsTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-hairline">
      <table className="w-full min-w-[56rem] text-left text-sm">
        <caption className="sr-only">Recorded sessions, newest first</caption>
        <thead className="text-xs uppercase tracking-wider text-fg2">
          <tr>
            {COLUMNS.map((name) => (
              <th key={name} scope="col" className="whitespace-nowrap px-3 py-2 font-semibold">
                {name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => {
            const selected = session.session_id === selectedId;
            return (
              <tr
                key={session.session_id}
                className={`border-t border-hairline ${selected ? "bg-hairline" : ""}`}
              >
                <th scope="row" className="whitespace-nowrap px-3 py-2 text-left font-medium">
                  <button
                    type="button"
                    aria-pressed={selected}
                    onClick={() => onSelect(session.session_id)}
                    className="spring rounded-md text-accent underline-offset-2 hover:underline"
                  >
                    {formatStarted(session.started_at)}
                  </button>
                </th>
                <td className="max-w-[18rem] truncate px-3 py-2" title={session.question ?? undefined}>
                  {session.question ?? NOT_REPORTED}
                </td>
                <td className="whitespace-nowrap px-3 py-2">{session.model ?? NOT_REPORTED}</td>
                <td className="px-3 py-2">{formatCount(session.turns)}</td>
                <td className="px-3 py-2">{formatCount(session.model_calls)}</td>
                <td className="px-3 py-2">{formatCount(session.tool_calls)}</td>
                <td className="whitespace-nowrap px-3 py-2">
                  {formatTokens(session.input_tokens, session.output_tokens)}
                </td>
                <td className="whitespace-nowrap px-3 py-2">{formatCost(session)}</td>
                <td className="whitespace-nowrap px-3 py-2">{formatDuration(session.duration_ms)}</td>
                <td className="px-3 py-2">
                  <OutcomePill outcome={session.outcome} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
