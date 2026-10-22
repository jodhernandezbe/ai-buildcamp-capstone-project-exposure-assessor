import { ChevronDown, ChevronUp } from "lucide-react";
import { useMemo, useState } from "react";

import { StatusPill } from "../../components/ui/StatusPill";
import { formatCount, formatNumber, formatRange } from "../../lib/format";
import type { Extreme, Facility } from "../../types/workspace";
import { OUTCOME_LABEL, type ResultRow, type SortDirection, type SortKey, sortRows, splitRows } from "./resultsRows";

interface Props {
  facilities: Facility[];
  digits: number;
  /** Asked to show a facility on the map (frame it and open its card). */
  onFocus?: (frsId: string) => void;
}

const COLUMNS: { key: SortKey; label: string; numeric: boolean }[] = [
  { key: "name", label: "Facility", numeric: false },
  { key: "status", label: "Status", numeric: false },
  { key: "emissionRate", label: "Emission rate (g/s)", numeric: true },
  { key: "hqWorst", label: "HQ, worst case", numeric: true },
  { key: "hqRepresentative", label: "HQ, representative", numeric: true },
  { key: "riskWorst", label: "Cancer risk, worst case", numeric: true },
  { key: "residents", label: "Residents", numeric: true },
];

const range = (extreme: Extreme | null, digits: number): string =>
  extreme ? formatRange(extreme.low, extreme.high, digits) : formatNumber(null, digits);

/** What a screened-out row shows in place of its worst-case HQ: the value it was left out on. */
function screenedOut(row: ResultRow, digits: number): string {
  const stage = row.outcome === "screened_out_at_bound" ? "bound" : "own stacks";
  const parts = [
    row.screenedHq !== null ? `HQ ${formatNumber(row.screenedHq, digits)}` : null,
    row.screenedRisk !== null ? `risk ${formatNumber(row.screenedRisk, digits)}` : null,
  ].filter(Boolean);
  return `screened out (${stage}${parts.length ? `: ${parts.join(", ")}` : ""})`;
}

function Row({ row, digits, onFocus }: { row: ResultRow; digits: number; onFocus?: (frsId: string) => void }) {
  const out = row.outcome.startsWith("screened_out");
  const label = row.name ?? `FRS ${row.frsId}`;
  return (
    <tr className="border-t border-hairline even:bg-fg2/[0.03]" data-frs-id={row.frsId}>
      <td className="px-2 py-1.5">
        <button
          type="button"
          onClick={onFocus ? () => onFocus(row.frsId) : undefined}
          className="spring rounded text-left font-medium text-fg hover:text-accent"
          aria-label={`Show ${label} on the map`}
        >
          {label}
        </button>
        <span className="block text-[11px] text-fg2">
          FRS {row.frsId}
          {row.state ? ` · ${row.state}` : ""} · {OUTCOME_LABEL[row.outcome]}
          {row.tier ? ` · ${row.tier}` : ""}
        </span>
      </td>
      <td className="px-2 py-1.5"><StatusPill status={row.status} /></td>
      <td className="whitespace-nowrap px-2 py-1.5 text-right">{formatNumber(row.emissionRate, digits)}</td>
      <td className="whitespace-nowrap px-2 py-1.5 text-right">{out ? screenedOut(row, digits) : range(row.hqWorst, digits)}</td>
      <td className="whitespace-nowrap px-2 py-1.5 text-right">{out ? "" : range(row.hqRepresentative, digits)}</td>
      <td className="whitespace-nowrap px-2 py-1.5 text-right">{out ? "" : range(row.riskWorst, digits)}</td>
      <td className="whitespace-nowrap px-2 py-1.5 text-right">{row.residents === null ? formatNumber(null, digits) : formatCount(row.residents)}</td>
    </tr>
  );
}

/**
 * Every facility the workspace holds, one row each, built from the state alone: the assessed
 * ones sorted by status then worst-case HQ (or by the column the user chose), and the
 * screened-out or unassessed ones folded below with their count.
 */
export function ResultsTable({ facilities, digits, onFocus }: Props) {
  const [sort, setSort] = useState<{ key: SortKey; direction: SortDirection }>({ key: "status", direction: "desc" });
  const { assessed, folded } = useMemo(() => splitRows(facilities), [facilities]);
  const rows = useMemo(() => sortRows(assessed, sort.key, sort.direction), [assessed, sort]);
  const foldedRows = useMemo(() => sortRows(folded, "status", "desc"), [folded]);
  const [showFolded, setShowFolded] = useState(false);
  if (facilities.length === 0) return null;
  const toggle = (key: SortKey) =>
    setSort((now) =>
      now.key === key ? { key, direction: now.direction === "desc" ? "asc" : "desc" } : { key, direction: key === "name" ? "asc" : "desc" },
    );
  return (
    <section aria-label="Results" className="glass mt-3 rounded-2xl p-3.5">
      <header className="mb-2 flex items-baseline justify-between gap-2">
        <h2 className="m-0 text-xs font-semibold uppercase tracking-wide text-fg2">Results</h2>
        <span className="text-xs text-fg2">
          {assessed.length} assessed · {folded.length} screened out or not assessed
        </span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-xs tabular-nums">
          <thead>
            <tr>
              {COLUMNS.map((column) => {
                const active = sort.key === column.key;
                const Icon = sort.direction === "desc" ? ChevronDown : ChevronUp;
                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={active ? (sort.direction === "desc" ? "descending" : "ascending") : "none"}
                    className={`px-2 py-1.5 font-semibold uppercase tracking-wider text-fg2 ${column.numeric ? "text-right" : "text-left"}`}
                  >
                    <button type="button" onClick={() => toggle(column.key)} className="inline-flex items-center gap-1 uppercase">
                      {column.label}
                      {active && <Icon size={12} aria-hidden="true" />}
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => <Row key={row.frsId} row={row} digits={digits} onFocus={onFocus} />)}
          </tbody>
        </table>
        {folded.length > 0 && (
          <div className="mt-2">
            <button
              type="button"
              aria-expanded={showFolded}
              onClick={() => setShowFolded((now) => !now)}
              className="text-xs text-fg2 hover:text-fg"
            >
              {showFolded ? "Hide" : "Show"} {folded.length} screened out or not assessed
            </button>
            {showFolded && (
              <table className="mt-1 w-full border-collapse text-xs tabular-nums">
                <tbody>
                  {foldedRows.map((row) => <Row key={row.frsId} row={row} digits={digits} onFocus={onFocus} />)}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
