import type { WorkspaceState } from "../../types/workspace";
import { DemographicsCard } from "./DemographicsCard";
import { MeteorologyCard } from "./MeteorologyCard";
import { ReadAcrossCard } from "./ReadAcrossCard";
import { RiskMetricCard } from "./RiskMetricCard";
import { WorkerRiskCard } from "./WorkerRiskCard";
import { WorstCaseSection } from "./WorstCaseSection";

/** The dose of the facility whose receptors the ribbon shows. */
function selectedDose(workspace: WorkspaceState) {
  const facility = workspace.facilities.find((f) => f.frs_id === workspace.selected_frs_id);
  return facility?.exposure?.dose ?? null;
}

/** The four summary cards, filled only from what the tools reported. */
export function EpaOverviewRibbon({ workspace, digits }: { workspace: WorkspaceState; digits: number }) {
  // An empty worst-case section takes only its content height (the first explicit row is
  // `auto`), so the summary cards are visible at first load; with data every row shares the panel.
  const firstRow = workspace.scenario_drivers.length === 0 ? "grid-rows-[auto]" : "";
  return (
    <div
      // Columns follow the panel's width (a container query), and the rows grow to fill its
      // height, so a fullscreen overview is four large cards rather than a strip at the top.
      className={`grid flex-1 auto-rows-[minmax(max-content,1fr)] grid-cols-1 gap-3 @2xl:grid-cols-2 ${firstRow}`}
      aria-label="Executive summary"
      role="group"
    >
      <div className="@2xl:col-span-2">
        <WorstCaseSection workspace={workspace} digits={digits} />
      </div>
      <RiskMetricCard risk={workspace.risk} digits={digits} />
      <WorkerRiskCard risk={workspace.worker_risk} digits={digits} />
      <ReadAcrossCard chemical={workspace.chemical} digits={digits} />
      <DemographicsCard receptors={workspace.receptors} dose={selectedDose(workspace)} digits={digits} />
      <MeteorologyCard weather={workspace.meteorology} digits={digits} />
    </div>
  );
}
