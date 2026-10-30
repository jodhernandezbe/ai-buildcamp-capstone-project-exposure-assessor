import type { Facility } from "../../types/workspace";

/** The facility to show: the pin while it is still in the workspace, else the chat's selection, else none. */
export function resolveFocus(
  facilities: readonly Facility[],
  selected: string | null,
  pinned: string | null,
): Facility | null {
  const find = (id: string | null) => facilities.find((facility) => facility.frs_id === id) ?? null;
  return find(pinned) ?? find(selected);
}
