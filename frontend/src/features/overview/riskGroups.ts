import { formatNumber, NOT_REPORTED } from "../../lib/format";
import type { Facility } from "../../types/workspace";
import { isAssessed, isScreenedOut } from "./assessment";

/** What facilities are grouped by: NAICS subsector, TSCA condition of use, TSCA life cycle stage. */
export type GroupBy = "subsector" | "condition" | "stage";
/** Which risk quotient orders the groups. */
export type RankBy = "hq" | "risk";
/** The two bars of a group. */
export type Quantity = RankBy;

/** The facility a bar comes from: one of the values the API sent, never a combination of them. */
export interface Best {
  value: number;
  frsId: string;
  name: string | null;
  /** That facility's worst-case concentration (µg/m³), when the API sent it. */
  concentration: number | null;
}

export interface Group {
  key: string;
  label: string;
  /** Facilities in the group, whatever became of them. */
  facilities: number;
  /** Of those, the ones with a worst-case result. */
  assessed: number;
  /** Of those, the ones screened out (their numbers are bounds, so they are never a bar). */
  screenedOut: number;
  hq: Best | null;
  risk: Best | null;
}

export interface Grouping {
  groups: Group[];
  /** Facilities that belong to no group (no subsector, no condition of use, no stage). */
  ungrouped: number;
}

export const TOP_N = 5;

const finite = (value: number | null | undefined): value is number =>
  typeof value === "number" && Number.isFinite(value);

function bestOf(current: Best | null, facility: Facility, value: number | null | undefined): Best | null {
  if (!finite(value) || (current !== null && value <= current.value)) return current;
  const concentration = facility.exposure?.concentration_worst?.high;
  return {
    value,
    frsId: facility.frs_id,
    name: facility.name,
    concentration: finite(concentration) ? concentration : null,
  };
}

/** The groups a facility belongs to: key and label of each, once per distinct key. */
function membership(facility: Facility, by: GroupBy): Map<string, string> {
  const found = new Map<string, string>();
  if (by === "subsector") {
    const code = facility.naics_subsector;
    if (code) found.set(code, facility.naics_subsector_title ? `${code} · ${facility.naics_subsector_title}` : code);
  } else if (by === "condition") {
    for (const c of facility.conditions_of_use) {
      const label = `${c.lifecycle_stage} · ${c.cou_category}`;
      found.set(label, label);
    }
  } else {
    for (const stage of facility.lifecycle_stages) found.set(stage, stage);
  }
  return found;
}

function emptyGroup(key: string, label: string): Group {
  return { key, label, facilities: 0, assessed: 0, screenedOut: 0, hq: null, risk: null };
}

function addTo(group: Group, facility: Facility): void {
  group.facilities += 1;
  if (isScreenedOut(facility)) group.screenedOut += 1;
  if (!isAssessed(facility)) return;
  group.assessed += 1;
  group.hq = bestOf(group.hq, facility, facility.exposure?.hq_worst?.high);
  group.risk = bestOf(group.risk, facility, facility.exposure?.cancer_risk_worst?.high);
}

/**
 * Group the facilities. A group's bars are the highest worst-case values among its assessed
 * facilities, selected from what the API sent; nothing is added, averaged or converted. A
 * facility is counted once per group it belongs to (several conditions of use are possible).
 */
export function groupFacilities(facilities: Facility[], by: GroupBy): Grouping {
  const groups = new Map<string, Group>();
  let ungrouped = 0;
  for (const facility of facilities) {
    const member = membership(facility, by);
    if (member.size === 0) ungrouped += 1;
    for (const [key, label] of member) {
      const group = groups.get(key) ?? emptyGroup(key, label);
      groups.set(key, group);
      addTo(group, facility);
    }
  }
  return { groups: [...groups.values()], ungrouped };
}

/** The `limit` groups with the highest value of the ranking quantity (ties by label). */
export function topGroups(
  groups: Group[],
  rankBy: RankBy,
  limit: number = TOP_N,
): { shown: Group[]; hidden: number } {
  const ranked = groups
    .filter((g) => g[rankBy] !== null)
    .sort((a, b) => (b[rankBy]?.value ?? 0) - (a[rankBy]?.value ?? 0) || a.label.localeCompare(b.label));
  return { shown: ranked.slice(0, limit), hidden: Math.max(ranked.length - limit, 0) };
}

const NAME: Record<Quantity, string> = { hq: "Hazard quotient", risk: "Lifetime cancer risk" };

/** The lines of a bar's tooltip. */
export function describeBar(group: Group, quantity: Quantity, digits: number): string[] {
  const best = group[quantity];
  const counts = `${group.facilities} ${group.facilities === 1 ? "facility" : "facilities"}, ${group.assessed} assessed`;
  const screened = group.screenedOut > 0 ? `, ${group.screenedOut} screened out` : "";
  if (best === null) {
    return [group.label, `${NAME[quantity]}: ${NOT_REPORTED}`, counts + screened];
  }
  return [
    group.label,
    `Highest ${NAME[quantity].toLowerCase()}: ${formatNumber(best.value, digits)}`,
    `Facility: ${best.name ?? "unnamed"} (FRS ${best.frsId})`,
    `Worst-case concentration: ${best.concentration === null ? NOT_REPORTED : `${formatNumber(best.concentration, digits)} µg/m³`}`,
    counts + screened,
  ];
}
