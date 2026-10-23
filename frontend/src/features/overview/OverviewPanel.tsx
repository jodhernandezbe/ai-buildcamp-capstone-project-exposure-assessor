import { useState, type KeyboardEvent } from "react";

import type { Thresholds } from "../../types/api";
import type { WorkspaceState } from "../../types/workspace";
import { EpaOverviewRibbon } from "./EpaOverviewRibbon";
import { isAssessed } from "./assessment";
import { RiskGroupSection } from "./RiskGroupSection";
import type { GroupBy, RankBy } from "./riskGroups";

interface Props {
  workspace: WorkspaceState;
  digits: number;
  /** Status thresholds from the client settings; the charts draw them as reference lines. */
  thresholds?: Thresholds;
}

type View = "summary" | "risk";

const SECTIONS: GroupBy[] = ["subsector", "condition", "stage"];
const VIEWS: { key: View; label: string }[] = [
  { key: "summary", label: "Summary" },
  { key: "risk", label: "Risk by group" },
];

function ViewSwitch({ view, onView }: { view: View; onView: (view: View) => void }) {
  return (
    <div role="group" aria-label="Overview view" className="mb-3 inline-flex self-start rounded-full bg-fg2/10 p-0.5 text-xs">
      {VIEWS.map(({ key, label }) => (
        <button
          key={key}
          type="button"
          aria-pressed={view === key}
          onClick={() => onView(key)}
          className={`spring rounded-full px-3 py-1 ${view === key ? "bg-solid font-medium text-fg shadow-sm" : "text-fg2 hover:text-fg"}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

/**
 * The Overview panel has two views of one workspace: the executive summary ribbon, and the three
 * risk-by-group charts (the switch is always there; the charts say what is missing). The ribbon stays
 * mounted; the charts are drawn only on their own view (Recharts cannot measure a hidden box), and
 * their ranking is kept here. A chart section can expand to fill the panel, hiding the others.
 */
export function OverviewPanel({ workspace, digits, thresholds }: Props) {
  const [view, setView] = useState<View>("summary");
  const [expanded, setExpanded] = useState<GroupBy | null>(null);
  const [rankBy, setRankBy] = useState<RankBy>("hq");
  const showRisk = view === "risk";
  const assessed = workspace.facilities.filter(isAssessed).length;
  const open = showRisk && expanded !== null;
  // Escape belongs to the topmost layer: restoring a section is handled here, so the panel's
  // fullscreen (a window listener that honours defaultPrevented) is not also left.
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Escape" || !open) return;
    event.preventDefault();
    event.stopPropagation();
    setExpanded(null);
  };
  // A flex column at least as tall as the panel, so the ribbon can stretch to fill it.
  return (
    <div className="@container flex min-h-full flex-col p-4 outline-none" tabIndex={-1} onKeyDown={onKeyDown}>
      <ViewSwitch view={view} onView={setView} />
      <div hidden={showRisk} className={showRisk ? "hidden" : "contents"}>
        <EpaOverviewRibbon workspace={workspace} digits={digits} />
      </div>
      {showRisk && (
        <>
          <p className="m-0 mb-2 text-xs text-fg2">
            {workspace.facilities.length} {workspace.facilities.length === 1 ? "facility" : "facilities"} in this run,{" "}
            {assessed} with a worst-case result.
          </p>
          <div className={open ? "flex min-h-0 flex-1 flex-col" : "grid grid-cols-1 gap-3 @4xl:grid-cols-3"}>
            {SECTIONS.map((by) => (
              <RiskGroupSection
                key={by}
                by={by}
                facilities={workspace.facilities}
                rankBy={rankBy}
                onRankBy={setRankBy}
                expanded={expanded === by}
                hidden={open && expanded !== by}
                onToggleExpand={() => setExpanded((now) => (now === by ? null : by))}
                thresholds={thresholds}
                digits={digits}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
