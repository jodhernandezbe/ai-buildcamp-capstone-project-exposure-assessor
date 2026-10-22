import { GlassCard } from "../../components/ui/GlassCard";
import type { FacilityFocus } from "../../hooks/useWorkspaceStore";
import type { ClientConfig, WorkspaceState } from "../../types/workspace";
import { ExposureMapCanvas } from "./ExposureMapCanvas";

interface Props {
  workspace: WorkspaceState;
  /** Changes when the camera should be reframed even if the workspace's framing did not. */
  viewEpoch: number;
  /** The facility to frame and open, when the overview asks for one. */
  focus?: FacilityFocus | null;
  digits: number;
  map: ClientConfig["map"] | undefined;
}

/** The facility map, filling the Map panel; a quiet placeholder until the map settings load. */
export function MapPanel({ workspace, viewEpoch, focus = null, digits, map }: Props) {
  return (
    <div className="h-full p-3">
      {map ? (
        <ExposureMapCanvas workspace={workspace} viewEpoch={viewEpoch} focus={focus} config={map} digits={digits} />
      ) : (
        <GlassCard className="grid h-full place-items-center p-6 text-sm text-fg2">Loading the map…</GlassCard>
      )}
    </div>
  );
}
