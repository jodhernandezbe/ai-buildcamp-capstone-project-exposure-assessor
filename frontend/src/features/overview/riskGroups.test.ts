import { describe, expect, it } from "vitest";

import { facility } from "../../test/fixtures";
import type { Facility } from "../../types/workspace";
import { describeBar, groupFacilities, topGroups } from "./riskGroups";

const extreme = (high: number) => ({ low: high / 2, high, low_stack: 1, high_stack: 2 });
const exposure = (hq: number | null, risk: number | null, conc: number | null = 10) => ({
  stacks_given: 1,
  stacks_evaluated: 1,
  hq_worst: hq === null ? null : extreme(hq),
  hq_representative: null,
  cancer_risk_worst: risk === null ? null : extreme(risk),
  cancer_risk_representative: null,
  concentration_worst: conc === null ? null : extreme(conc),
  concentration_representative: null,
  warnings: [],
});
const cond = (stage: string, category: string) => ({
  tri_activity: "x", tri_section: "3.2a", lifecycle_stage: stage, cou_category: category, mapping_strength: "Direct",
});
/** A value a test knows exists. */
function must<T>(value: T | undefined): T {
  if (value === undefined) throw new Error("expected a value");
  return value;
}
const make = (id: string, over: Partial<Facility>): Facility => facility({ frs_id: id, name: `Plant ${id}`, ...over });
const sub = (code: string | null, title: string | null = "Title") => ({ naics_subsector: code, naics_subsector_title: title });
const screenedOut = { outcome: "screened_out_at_bound" as const, bound_hq: 0.1, bound_cancer_risk: null, value_hq: 0.1, value_cancer_risk: null, reason: "r" };

describe("groupFacilities by subsector", () => {
  const facilities = [
    make("A", { ...sub("325", "Chemicals"), exposure: exposure(2, 1e-6, 4) }),
    make("B", { ...sub("325", "Chemicals"), exposure: exposure(5, 1e-7, 8) }),
    make("C", { ...sub("324", "Petroleum"), exposure: exposure(0.5, null) }),
    make("D", sub(null, null)),
  ];

  it("takes the highest value of each quantity from one facility, never a combination", () => {
    const chem = must(groupFacilities(facilities, "subsector").groups.find((g) => g.key === "325"));
    expect(chem.label).toBe("325 · Chemicals");
    expect(chem.hq).toEqual({ value: 5, frsId: "B", name: "Plant B", concentration: 8 });
    expect(chem.risk).toEqual({ value: 1e-6, frsId: "A", name: "Plant A", concentration: 4 });
    expect([chem.facilities, chem.assessed]).toEqual([2, 2]);
  });

  it("counts a facility with no subsector as ungrouped, not as a group", () => {
    const result = groupFacilities(facilities, "subsector");
    expect(result.ungrouped).toBe(1);
    expect(result.groups.map((g) => g.key).sort()).toEqual(["324", "325"]);
  });

  it("labels a subsector without a title by its code", () => {
    const [group] = groupFacilities([make("A", sub("999", null))], "subsector").groups;
    expect(group?.label).toBe("999");
  });
});

describe("assessed and screened-out facilities", () => {
  it("leaves screened-out and unassessed facilities out of the bars but counts them", () => {
    const facilities = [
      make("A", { ...sub("325"), exposure: exposure(1, null) }),
      make("B", { ...sub("325"), screening: screenedOut }),
      make("C", sub("325")),
    ];
    const [g] = groupFacilities(facilities, "subsector").groups;
    expect([g?.facilities, g?.assessed, g?.screenedOut]).toEqual([3, 1, 1]);
    expect(g?.hq?.frsId).toBe("A");
  });

  it("has no bar for a group where nothing was assessed", () => {
    const [g] = groupFacilities([make("B", { ...sub("325"), screening: screenedOut })], "subsector").groups;
    expect(g?.hq).toBeNull();
    expect(topGroups([must(g)], "hq").shown).toEqual([]);
  });

  it("ignores non-finite values", () => {
    const [g] = groupFacilities([make("A", { ...sub("325"), exposure: exposure(Number.NaN, Number.POSITIVE_INFINITY) })], "subsector").groups;
    expect([g?.hq, g?.risk]).toEqual([null, null]);
  });

  it("keeps a concentration that was not sent as null", () => {
    const [g] = groupFacilities([make("A", { ...sub("325"), exposure: exposure(2, null, null) })], "subsector").groups;
    expect(g?.hq?.concentration).toBeNull();
  });
});

describe("groupFacilities by condition of use and stage", () => {
  const two = make("A", {
    exposure: exposure(3, null),
    conditions_of_use: [cond("Processing", "Reactant"), cond("Industrial use", "Function")],
    lifecycle_stages: ["Processing", "Industrial use"],
  });

  it("puts a facility in every one of its conditions, once each", () => {
    const duplicated = make("B", {
      exposure: exposure(1, null),
      conditions_of_use: [cond("Processing", "Reactant"), cond("Processing", "Reactant")],
      lifecycle_stages: ["Processing"],
    });
    const result = groupFacilities([two, duplicated], "condition");
    const reactant = must(result.groups.find((g) => g.key === "Processing · Reactant"));
    expect(reactant.facilities).toBe(2);
    expect(result.groups).toHaveLength(2);
  });

  it("groups by life cycle stage", () => {
    const stages = groupFacilities([two, make("C", {})], "stage");
    expect(stages.groups.map((g) => g.key)).toEqual(["Processing", "Industrial use"]);
    expect(stages.ungrouped).toBe(1);
  });
});

describe("topGroups", () => {
  const many = ["a", "b", "c", "d", "e", "f", "g"].map((k, i) =>
    make(k, { ...sub(`3${i}${i}`, `Title ${k}`), exposure: exposure(i + 1, 10 - i) }),
  );
  const groups = groupFacilities(many, "subsector").groups;

  it("keeps the five highest hazard quotients, highest first, and says how many were cut", () => {
    const { shown, hidden } = topGroups(groups, "hq");
    expect(shown.map((g) => g.hq?.value)).toEqual([7, 6, 5, 4, 3]);
    expect(hidden).toBe(2);
  });

  it("re-ranks by cancer risk", () => {
    expect(topGroups(groups, "risk").shown.map((g) => g.risk?.value)).toEqual([10, 9, 8, 7, 6]);
  });

  it("breaks ties by label and drops groups without the ranking value", () => {
    const tied = groupFacilities(
      [
        make("A", { ...sub("200", "Zeta"), exposure: exposure(1, null) }),
        make("B", { ...sub("100", "Alpha"), exposure: exposure(1, null) }),
        make("C", { ...sub("300", "Mid"), exposure: exposure(null, 1e-5) }),
      ],
      "subsector",
    ).groups;
    expect(topGroups(tied, "hq").shown.map((g) => g.label)).toEqual(["100 · Alpha", "200 · Zeta"]);
    expect(topGroups(tied, "risk").shown.map((g) => g.label)).toEqual(["300 · Mid"]);
  });
});

describe("describeBar", () => {
  const [group] = groupFacilities(
    [
      make("A", { ...sub("325", "Chemicals"), exposure: exposure(5, null, 12) }),
      make("B", { ...sub("325", "Chemicals"), screening: screenedOut }),
    ],
    "subsector",
  ).groups;

  it("names the value, the facility, its concentration and the counts", () => {
    expect(describeBar(must(group), "hq", 2)).toEqual([
      "325 · Chemicals",
      "Highest hazard quotient: 5",
      "Facility: Plant A (FRS A)",
      "Worst-case concentration: 12 µg/m³",
      "2 facilities, 1 assessed, 1 screened out",
    ]);
  });

  it("says not reported for a quantity the group has no value for", () => {
    expect(describeBar(must(group), "risk", 2)).toEqual([
      "325 · Chemicals",
      "Lifetime cancer risk: not reported",
      "2 facilities, 1 assessed, 1 screened out",
    ]);
  });
});
