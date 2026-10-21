import { GlassCard } from "../../components/ui/GlassCard";
import type { ClientConfig, WorkspaceState } from "../../types/workspace";
import { ExposureMapCanvas } from "../map/ExposureMapCanvas";
import { EpaOverviewRibbon } from "./EpaOverviewRibbon";

interface Props {
  workspace: WorkspaceState;
  digits: number;
  map: ClientConfig["map"] | undefined;
}

/** The left pane: the executive summary ribbon above the facility map. */
export function OverviewPane({ workspace, digits, map }: Props) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-3 overflow-y-auto p-4">
      <EpaOverviewRibbon workspace={workspace} digits={digits} />
      <div className="min-h-96 flex-1">
        {map ? (
          <ExposureMapCanvas workspace={workspace} config={map} digits={digits} />
        ) : (
          <GlassCard className="grid h-full place-items-center p-6 text-sm text-fg2">
            Loading the map…
          </GlassCard>
        )}
      </div>
    </div>
  );
}
