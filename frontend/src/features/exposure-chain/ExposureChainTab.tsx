import { useId, useState, type KeyboardEvent } from "react";

import { GlassCard } from "../../components/ui/GlassCard";
import { StatusPill } from "../../components/ui/StatusPill";
import type { Facility, WorkspaceState } from "../../types/workspace";
import { ChainCanvas } from "./ChainCanvas";
import { DetailPanel } from "./DetailPanel";
import { drawnLanes, formatQuantity, visibleGraph, type ExposureGraph } from "./graph";
import { useGraphLayout } from "./useGraphLayout";

interface Props {
  /** The facility being looked at (a map pin, the picker, or the chat's selection). */
  facility: Facility | null;
  workspace: WorkspaceState;
  digits: number;
  onPick: (frsId: string) => void;
}

function LanePicker({ graph, value, onChange }: { graph: ExposureGraph; value: string; onChange: (lane: string) => void }) {
  const items = [{ id: "all", label: "All pathways" }, ...drawnLanes(graph)];
  if (items.length <= 2) return null;
  return (
    <div role="group" aria-label="Pathway" className="inline-flex rounded-full bg-fg2/10 p-0.5 text-xs">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          aria-pressed={item.id === value}
          onClick={() => onChange(item.id)}
          className={`spring rounded-full px-3 py-1 ${item.id === value ? "bg-solid font-medium text-fg shadow-sm" : "text-fg2 hover:text-fg"}`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

function FacilityPicker({ workspace, facility, onPick }: { workspace: WorkspaceState; facility: Facility; onPick: (id: string) => void }) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-fg2">
      Facility
      <select value={facility.frs_id} onChange={(e) => onPick(e.target.value)} className="max-w-64 rounded-lg bg-fg2/10 px-2 py-1 text-xs text-fg">
        {workspace.facilities.map((f) => (
          <option key={f.frs_id} value={f.frs_id}>
            {f.name ?? f.frs_id}
          </option>
        ))}
      </select>
    </label>
  );
}

function LaneStatus({ graph }: { graph: ExposureGraph }) {
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-xs text-fg2" aria-label="Pathways">
      {graph.lanes.map((lane) => (
        <li key={lane.id} className="flex items-center gap-1.5">
          <span className="text-fg">{lane.label}</span>
          {lane.available ? <StatusPill status={lane.status} label={lane.status_label ?? undefined} /> : <span>({lane.reason})</span>}
        </li>
      ))}
    </ul>
  );
}

/** What a screen reader gets instead of the picture: every connection with what it carries. */
function Connections({ graph, digits }: { graph: ExposureGraph; digits: number }) {
  const title = new Map(graph.nodes.map((n) => [n.id, n.title]));
  return (
    <ol className="sr-only" aria-label="Connections">
      {graph.edges.map((e) => (
        <li key={e.id}>
          {`${title.get(e.source) ?? e.source} to ${title.get(e.target) ?? e.target}`}
          {e.quantity ? `: ${e.quantity.label} ${formatQuantity(e.quantity, digits)}` : ""}
        </li>
      ))}
    </ol>
  );
}

function Empty({ text }: { text: string }) {
  return <GlassCard className="p-4 text-sm text-fg2">{text}</GlassCard>;
}

/**
 * The Exposure chain tab: the facility's exposure graph as the API built it, laid out left to right
 * (source, releases, pathways, routes, receptors, endpoints) with flowing, labelled connections.
 */
export function ExposureChainTab({ facility, workspace, digits, onPick }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredLane, setHoveredLane] = useState<string | null>(null);
  const [lane, setLane] = useState("all");
  const detailId = useId();
  const full = facility?.exposure_graph ?? null;
  const graph = full ? visibleGraph(full, full.lanes.some((l) => l.id === lane) ? lane : "all") : null;
  const { positions, key } = useGraphLayout(graph);
  if (!facility) return <Empty text="No facility selected. Run an assessment, or click a facility on the map, to see its exposure chain." />;
  if (!full || !graph) return <Empty text="This facility has no exposure chain yet; it appears once the facility is assessed." />;
  const selected = graph.nodes.find((n) => n.id === selectedId) ?? null;
  const activeLane = hoveredLane ?? selected?.lane ?? null;
  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Escape" || !selected) return;
    event.preventDefault();
    event.stopPropagation();
    setSelectedId(null);
  };
  return (
    <section aria-label="Exposure chain" className="flex min-h-0 flex-1 flex-col gap-3" onKeyDown={onKeyDown}>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <FacilityPicker workspace={workspace} facility={facility} onPick={onPick} />
        <LanePicker graph={full} value={lane} onChange={setLane} />
        <LaneStatus graph={full} />
      </div>
      <div className="relative min-h-[440px] flex-1 overflow-hidden rounded-xl border border-hairline bg-fg2/5">
        {positions ? (
          <ChainCanvas
            graph={graph}
            positions={positions}
            layoutKey={key}
            digits={digits}
            selectedId={selected?.id ?? null}
            activeLane={activeLane}
            detailId={detailId}
            onSelect={(id) => setSelectedId((now) => (now === id ? null : id))}
            onHover={setHoveredLane}
          />
        ) : (
          <p className="m-0 p-4 text-xs text-fg2">Laying out the chain…</p>
        )}
      </div>
      <DetailPanel
        node={selected}
        laneLabel={full.lanes.find((l) => l.id === selected?.lane)?.label ?? null}
        digits={digits}
        id={detailId}
        onClose={() => setSelectedId(null)}
      />
      <Connections graph={graph} digits={digits} />
    </section>
  );
}
