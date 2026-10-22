import { describe, expect, it } from "vitest";

import { facility } from "../../test/fixtures";
import { isAssessed, sortRows, splitRows, toRow } from "./resultsRows";

const extreme = (high: number) => ({ low: high / 2, high, low_stack: 1, high_stack: 2 });
const exposure = (hq: number) => ({
  stacks_given: 2,
  stacks_evaluated: 2,
  hq_worst: extreme(hq),
  hq_representative: extreme(hq / 10),
  cancer_risk_worst: null,
  cancer_risk_representative: null,
  concentration_worst: null,
  concentration_representative: null,
  warnings: [],
});
const screening = (outcome: "screened_out_at_bound" | "worst_case_only", hq: number | null) => ({
  outcome,
  bound_hq: hq,
  bound_cancer_risk: null,
  value_hq: hq,
  value_cancer_risk: null,
  reason: null,
});

describe("toRow", () => {
  it("takes the outcome from the screening, else from whether a risk exists", () => {
    expect(toRow(facility()).outcome).toBe("not_assessed");
    expect(toRow(facility({ exposure: exposure(2) })).outcome).toBe("full");
    const screened = facility({ screening: screening("screened_out_at_bound", 0.05) });
    expect(toRow(screened)).toMatchObject({ outcome: "screened_out_at_bound", screenedHq: 0.05 });
    expect(toRow(facility({ exposure: exposure(2) })).screenedHq).toBeNull();
  });

  it("copies values as sent and leaves absent ones null", () => {
    const row = toRow(facility({ exposure: exposure(2), receptors: null }));
    expect(row.hqWorst?.high).toBe(2);
    expect(row.residents).toBeNull();
    expect(row.tier).toBeNull();
  });
});

describe("splitRows and sortRows", () => {
  const above = facility({ frs_id: "A", name: "Alpha", status: "above", exposure: exposure(5) });
  const near = facility({ frs_id: "N", name: "Near", status: "near", exposure: exposure(0.5) });
  const big = facility({ frs_id: "B", name: "Big", status: "above", exposure: exposure(9) });
  const worst = facility({ frs_id: "W", status: "below", exposure: exposure(0.01), screening: screening("worst_case_only", null) });
  const out = facility({ frs_id: "O", status: "below", screening: screening("screened_out_at_bound", 0.02) });
  const none = facility({ frs_id: "X" });

  it("folds screened-out and unassessed facilities below the assessed ones", () => {
    const { assessed, folded } = splitRows([above, out, worst, none]);
    expect(assessed.map((r) => r.frsId)).toEqual(["A", "W"]);
    expect(folded.map((r) => r.frsId)).toEqual(["O", "X"]);
    expect(assessed.every(isAssessed) && !folded.some(isAssessed)).toBe(true);
  });

  it("orders by status then worst-case HQ by default, highest first", () => {
    const rows = sortRows(splitRows([near, above, big]).assessed, "status", "desc");
    expect(rows.map((r) => r.frsId)).toEqual(["B", "A", "N"]);
  });

  it("sorts by a column in either direction with absent values last", () => {
    const rows = splitRows([above, big, worst]).assessed;
    expect(sortRows(rows, "name", "asc").map((r) => r.frsId)).toEqual(["A", "B", "W"]);
    expect(sortRows(rows, "hqWorst", "asc").map((r) => r.frsId)).toEqual(["W", "A", "B"]);
    const residents = sortRows(rows, "residents", "desc").map((r) => r.residents);
    expect(residents.every((r) => r === null)).toBe(true);
  });

  it("does not change the rows it was given", () => {
    const rows = splitRows([above, big]).assessed;
    const before = rows.map((r) => r.frsId);
    sortRows(rows, "hqWorst", "desc");
    expect(rows.map((r) => r.frsId)).toEqual(before);
  });
});
