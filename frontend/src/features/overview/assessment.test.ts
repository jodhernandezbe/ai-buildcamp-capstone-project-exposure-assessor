import { describe, expect, it } from "vitest";

import { facility } from "../../test/fixtures";
import type { Facility } from "../../types/workspace";
import { isAssessed, isScreenedOut, outcomeOf } from "./assessment";

const screening = (outcome: NonNullable<Facility["screening"]>["outcome"]): Facility["screening"] => ({
  outcome,
  bound_hq: null,
  bound_cancer_risk: null,
  value_hq: null,
  value_cancer_risk: null,
  reason: "r",
});
const exposure = {
  stacks_given: 1,
  stacks_evaluated: 1,
  hq_worst: null,
  hq_representative: null,
  cancer_risk_worst: null,
  cancer_risk_representative: null,
  concentration_worst: null,
  concentration_representative: null,
  dose: null,
  warnings: [],
};

describe("assessment outcome", () => {
  it("is not assessed when nothing was computed and the screen said nothing", () => {
    const f = facility({});
    expect([outcomeOf(f), isAssessed(f), isScreenedOut(f)]).toEqual(["not_assessed", false, false]);
  });

  it("is a full assessment when an exposure exists and the screen said nothing", () => {
    const f = facility({ exposure });
    expect([outcomeOf(f), isAssessed(f), isScreenedOut(f)]).toEqual(["full", true, false]);
  });

  it.each([
    ["full", true, false],
    ["worst_case_only", true, false],
    ["screened_out_at_bound", false, true],
    ["screened_out_with_own_stacks", false, true],
    ["not_assessed", false, false],
  ] as const)("follows the screen's outcome %s", (outcome, assessed, screened) => {
    const f = facility({ screening: screening(outcome), exposure });
    expect([outcomeOf(f), isAssessed(f), isScreenedOut(f)]).toEqual([outcome, assessed, screened]);
  });
});
