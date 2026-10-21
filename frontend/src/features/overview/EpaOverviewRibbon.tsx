import type { WorkspaceState } from "../../types/workspace";
import { DemographicsCard } from "./DemographicsCard";
import { MeteorologyCard } from "./MeteorologyCard";
import { ReadAcrossCard } from "./ReadAcrossCard";
import { RiskMetricCard } from "./RiskMetricCard";

/** The four summary cards, filled only from what the tools reported. */
export function EpaOverviewRibbon({ workspace, digits }: { workspace: WorkspaceState; digits: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4" aria-label="Executive summary" role="group">
      <RiskMetricCard risk={workspace.risk} digits={digits} />
      <ReadAcrossCard chemical={workspace.chemical} digits={digits} />
      <DemographicsCard receptors={workspace.receptors} digits={digits} />
      <MeteorologyCard weather={workspace.meteorology} digits={digits} />
    </div>
  );
}
