import { GlassCard } from "../../components/ui/GlassCard";
import type { ClientConfig, WorkspaceState } from "../../types/workspace";
import { ExposureMapCanvas } from "./ExposureMapCanvas";

interface Props {
  workspace: WorkspaceState;
  /** Changes when the camera should be reframed even if the workspace's framing did not. */
  viewEpoch: number;
  digits: number;
  map: ClientConfig["map"] | undefined;
  /** Told which facility the user pinned on the map. */
  onPin?: (frsId: string) => void;
}

/** The facility map, filling the Map panel; a quiet placeholder until the map settings load. */
export function MapPanel({ workspace, viewEpoch, digits, map, onPin }: Props) {
  return (
    <div className="h-full p-3">
      {map ? (
        <ExposureMapCanvas workspace={workspace} viewEpoch={viewEpoch} config={map} digits={digits} onPin={onPin} />
      ) : (
        <GlassCard className="grid h-full place-items-center p-6 text-sm text-fg2">Loading the map…</GlassCard>
      )}
    </div>
  );
}
