import type { WorkspaceState } from "../../types/workspace";
import { EpaOverviewRibbon } from "./EpaOverviewRibbon";
import { ResultsTable } from "./ResultsTable";

interface Props {
  workspace: WorkspaceState;
  digits: number;
  /** Asked to show a facility on the map (frame it and open its card). */
  onFocusFacility?: (frsId: string) => void;
}

/** The executive summary ribbon and the results table, shown inside the Overview panel. */
export function OverviewPanel({ workspace, digits, onFocusFacility }: Props) {
  // A flex column at least as tall as the panel, so the ribbon can stretch to fill it.
  return (
    <div className="@container flex min-h-full flex-col p-4">
      <EpaOverviewRibbon workspace={workspace} digits={digits} />
      <ResultsTable facilities={workspace.facilities} digits={digits} onFocus={onFocusFacility} />
    </div>
  );
}
