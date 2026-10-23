import type { Ref } from "react";

import type { Facility, Status } from "../../types/workspace";

export const SECTOR_CAPTION = "schematic downwind sector, not a modelled plume footprint";

/** A marker's status key: its risk status, or "none" while no risk is computed. */
export type StatusKey = NonNullable<Status> | "none";

const ITEMS: { key: StatusKey; label: string; tone: string }[] = [
  { key: "below", label: "Below concern", tone: "bg-ok" },
  { key: "near", label: "Near concern", tone: "bg-warn" },
  { key: "above", label: "Above concern", tone: "bg-bad" },
  { key: "none", label: "Not computed", tone: "bg-fg2" },
];

export const statusKey = (facility: Facility): StatusKey => facility.status ?? "none";

interface Props {
  facilities: Facility[];
  /** Status keys whose markers are hidden; clicking a legend entry toggles one. */
  hidden: ReadonlySet<StatusKey>;
  onToggle: (key: StatusKey) => void;
  ref?: Ref<HTMLElement>;
}

/** What the marker colours and sizes mean; each entry shows or hides its markers. */
export function MapLegend({ facilities, hidden, onToggle, ref }: Props) {
  const showsSector = facilities.some((f) => f.sector !== null);
  const counts = new Map<StatusKey, number>();
  for (const facility of facilities) {
    const key = statusKey(facility);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return (
    <aside
      ref={ref}
      aria-label="Map legend"
      className="glass absolute bottom-3 left-3 z-10 max-w-64 rounded-xl p-2.5 text-xs"
    >
      <ul className="m-0 grid list-none gap-0.5 p-0">
        {ITEMS.map((item) => {
          const off = hidden.has(item.key);
          const count = counts.get(item.key) ?? 0;
          return (
            <li key={item.key}>
              <button
                type="button"
                aria-pressed={!off}
                onClick={() => onToggle(item.key)}
                title={off ? `Show ${item.label.toLowerCase()} markers` : `Hide ${item.label.toLowerCase()} markers`}
                className={`spring flex w-full items-center gap-1.5 rounded px-1 py-0.5 text-left transition hover:bg-fg2/10 ${off ? "opacity-40" : ""}`}
              >
                <span aria-hidden className={`inline-block size-2.5 shrink-0 rounded-full ${item.tone}`} />
                <span className={off ? "line-through" : ""}>{item.label}</span>
                <span className="ml-auto pl-1.5 text-fg2">{count}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="m-0 mt-1.5 text-fg2">Marker size follows the emission rate (g/s).</p>
      <p className="m-0 mt-1 text-fg2">Click an entry to hide or show its markers.</p>
      {showsSector && <p className="m-0 mt-1 text-warn">Shaded wedge: {SECTOR_CAPTION}.</p>}
    </aside>
  );
}
