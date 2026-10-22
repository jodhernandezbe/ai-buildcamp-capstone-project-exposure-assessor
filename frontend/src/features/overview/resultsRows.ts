import type { Extreme, Facility } from "../../types/workspace";

type Status = Facility["status"];

/** What became of a facility in the assessment; "not_assessed" when nothing was computed. */
export type Outcome =
  | "full"
  | "worst_case_only"
  | "screened_out_at_bound"
  | "screened_out_with_own_stacks"
  | "not_assessed";

/** One facility as the results table shows it: values only as the API sent them. */
export interface ResultRow {
  frsId: string;
  name: string | null;
  state: string | null;
  emissionRate: number;
  outcome: Outcome;
  tier: string | null;
  hqWorst: Extreme | null;
  hqRepresentative: Extreme | null;
  riskWorst: Extreme | null;
  riskRepresentative: Extreme | null;
  residents: number | null;
  status: Status;
  /** The value a screened-out facility was left out on (HQ, cancer risk); null otherwise. */
  screenedHq: number | null;
  screenedRisk: number | null;
}

export type SortKey = "status" | "name" | "emissionRate" | "hqWorst" | "hqRepresentative" | "riskWorst" | "residents";
export type SortDirection = "asc" | "desc";

const STATUS_RANK: Record<NonNullable<Status> | "none", number> = { above: 3, near: 2, below: 1, none: 0 };

export const OUTCOME_LABEL: Record<Outcome, string> = {
  full: "Fully assessed",
  worst_case_only: "Worst case only",
  screened_out_at_bound: "Screened out on the bound",
  screened_out_with_own_stacks: "Screened out with its own stacks",
  not_assessed: "Not assessed",
};

function outcomeOf(facility: Facility): Outcome {
  if (facility.screening) return facility.screening.outcome;
  return facility.exposure ? "full" : "not_assessed";
}

/** A facility's row; nothing is computed, converted or estimated here. */
export function toRow(facility: Facility): ResultRow {
  const outcome = outcomeOf(facility);
  const screened = outcome.startsWith("screened_out") ? facility.screening : null;
  return {
    frsId: facility.frs_id,
    name: facility.name,
    state: facility.state,
    emissionRate: facility.emission_rate_g_s,
    outcome,
    tier: facility.stacks[0]?.tier_label ?? null,
    hqWorst: facility.exposure?.hq_worst ?? null,
    hqRepresentative: facility.exposure?.hq_representative ?? null,
    riskWorst: facility.exposure?.cancer_risk_worst ?? null,
    riskRepresentative: facility.exposure?.cancer_risk_representative ?? null,
    residents: facility.receptors?.total_population ?? null,
    status: facility.status,
    screenedHq: screened?.value_hq ?? null,
    screenedRisk: screened?.value_cancer_risk ?? null,
  };
}

/** Whether the row belongs with the assessed facilities (else it folds below them). */
export const isAssessed = (row: ResultRow): boolean =>
  row.outcome === "full" || row.outcome === "worst_case_only";

const high = (extreme: Extreme | null): number => extreme?.high ?? Number.NEGATIVE_INFINITY;

/** The sort value of a row for a key; absent values sort last in either direction. */
function valueOf(row: ResultRow, key: SortKey): number | string {
  switch (key) {
    case "status":
      return STATUS_RANK[row.status ?? "none"];
    case "name":
      return (row.name ?? "").toLowerCase();
    case "emissionRate":
      return row.emissionRate;
    case "hqWorst":
      return high(row.hqWorst);
    case "hqRepresentative":
      return high(row.hqRepresentative);
    case "riskWorst":
      return high(row.riskWorst);
    case "residents":
      return row.residents ?? Number.NEGATIVE_INFINITY;
  }
}

const compare = (a: number | string, b: number | string): number =>
  typeof a === "string" || typeof b === "string" ? String(a).localeCompare(String(b)) : a - b;

/**
 * Rows in the order asked for: the key, then (ties) the status and the worst-case HQ, highest
 * first. The default order is `status` descending, which puts facilities above concern first.
 */
export function sortRows(rows: ResultRow[], key: SortKey, direction: SortDirection): ResultRow[] {
  const sign = direction === "desc" ? -1 : 1;
  return [...rows].sort((a, b) => {
    const primary = compare(valueOf(a, key), valueOf(b, key)) * sign;
    if (primary !== 0) return primary;
    const byStatus = compare(valueOf(b, "status"), valueOf(a, "status"));
    return byStatus !== 0 ? byStatus : compare(valueOf(b, "hqWorst"), valueOf(a, "hqWorst"));
  });
}

/** The table's two groups: assessed facilities, and those screened out or not assessed. */
export function splitRows(facilities: Facility[]): { assessed: ResultRow[]; folded: ResultRow[] } {
  const rows = facilities.map(toRow);
  return { assessed: rows.filter(isAssessed), folded: rows.filter((row) => !isAssessed(row)) };
}
