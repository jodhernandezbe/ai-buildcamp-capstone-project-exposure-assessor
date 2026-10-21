import type { Ref } from "react";

import type { Facility } from "../../types/workspace";

export const SECTOR_CAPTION = "schematic downwind sector — not a modelled plume footprint";

const ITEMS = [
  { label: "Below concern", tone: "bg-ok" },
  { label: "Near concern", tone: "bg-warn" },
  { label: "Above concern", tone: "bg-bad" },
  { label: "Not computed", tone: "bg-fg2" },
];

/** What the marker colours and sizes mean, and the caveat on the downwind sector. */
export function MapLegend({ facilities, ref }: { facilities: Facility[]; ref?: Ref<HTMLElement> }) {
  const showsSector = facilities.some((f) => f.sector !== null);
  return (
    <aside
      ref={ref}
      aria-label="Map legend"
      className="glass absolute bottom-3 left-3 z-10 max-w-64 rounded-xl p-2.5 text-xs"
    >
      <ul className="m-0 grid list-none gap-1 p-0">
        {ITEMS.map((item) => (
          <li key={item.label} className="flex items-center gap-1.5">
            <span aria-hidden className={`inline-block size-2.5 rounded-full ${item.tone}`} />
            {item.label}
          </li>
        ))}
      </ul>
      <p className="m-0 mt-1.5 text-fg2">Marker size follows the emission rate (g/s).</p>
      {showsSector && <p className="m-0 mt-1 text-warn">Shaded wedge: {SECTOR_CAPTION}.</p>}
    </aside>
  );
}
