import type { WorkspaceState } from "../../types/workspace";
import { DemographicsCard } from "./DemographicsCard";
import { MeteorologyCard } from "./MeteorologyCard";
import { ReadAcrossCard } from "./ReadAcrossCard";
import { RiskMetricCard } from "./RiskMetricCard";

/** The four summary cards, filled only from what the tools reported. */
export function EpaOverviewRibbon({ workspace, digits }: { workspace: WorkspaceState; digits: number }) {
  return (
    <div
      // Columns follow the panel's width (a container query), and the rows grow to fill its
      // height, so a fullscreen overview is four large cards rather than a strip at the top.
      className="grid flex-1 auto-rows-[minmax(max-content,1fr)] grid-cols-1 gap-3 @2xl:grid-cols-2"
      aria-label="Executive summary"
      role="group"
    >
      <RiskMetricCard risk={workspace.risk} digits={digits} />
      <ReadAcrossCard chemical={workspace.chemical} digits={digits} />
      <DemographicsCard receptors={workspace.receptors} digits={digits} />
      <MeteorologyCard weather={workspace.meteorology} digits={digits} />
    </div>
  );
}
