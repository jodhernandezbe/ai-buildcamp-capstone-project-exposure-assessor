import { useCallback, useState } from "react";

import type { Facility, WorkspaceState } from "../../types/workspace";
import { resolveFocus } from "./focus";

/**
 * The facility the chain shows: the last one pinned on the map, else the chat's selection.
 * The pin is dropped for good when the chat selects another facility or the workspace is replaced
 * (`epoch`), so it cannot come back if the selection later returns to an earlier value.
 */
export function useFocusedFacility(workspace: WorkspaceState, epoch: number) {
  const selected = workspace.selected_frs_id;
  const [pinned, setPinned] = useState<string | null>(null);
  const [seen, setSeen] = useState({ selected, epoch });
  if (seen.selected !== selected || seen.epoch !== epoch) {
    // Adjusting state while rendering (React's documented pattern) avoids a frame with a stale pin.
    setSeen({ selected, epoch });
    setPinned(null);
  }
  const onPin = useCallback((frsId: string) => setPinned(frsId), []);
  const facility: Facility | null = resolveFocus(workspace.facilities, selected, pinned);
  return { facility, onPin };
}
