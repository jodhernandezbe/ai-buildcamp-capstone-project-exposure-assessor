import type { WorkspaceState } from "../../types/workspace";
import { EpaOverviewRibbon } from "./EpaOverviewRibbon";

interface Props {
  workspace: WorkspaceState;
  digits: number;
}

/** The executive summary ribbon, shown inside the Overview panel. */
export function OverviewPanel({ workspace, digits }: Props) {
  // A flex column at least as tall as the panel, so the ribbon can stretch to fill it.
  return (
    <div className="@container flex min-h-full flex-col p-4">
      <EpaOverviewRibbon workspace={workspace} digits={digits} />
    </div>
  );
}
