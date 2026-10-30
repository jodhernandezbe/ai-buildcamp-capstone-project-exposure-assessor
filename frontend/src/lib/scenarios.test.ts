import { describe, expect, it } from "vitest";

import { facility, scenario } from "../test/fixtures";
import type { ScenarioFactor } from "../types/workspace";
import { factorValue, groupFactors, ranking, scenarioFor, stackNumber } from "./scenarios";

const factor = (over: Partial<ScenarioFactor>): ScenarioFactor => ({
  key: "k",
  group: "source",
  label: "Label",
  value: 1,
  unit: "",
  source: null,
  reason: null,
  ...over,
});

describe("groupFactors", () => {
  it("keeps the told order and leaves out empty groups", () => {
    const groups = groupFactors([
      factor({ key: "a", group: "conditions" }),
      factor({ key: "b", group: "source" }),
      factor({ key: "c", group: "conditions" }),
    ]);
    expect(groups.map((g) => g.key)).toEqual(["source", "conditions"]);
    expect(groups[1]?.factors.map((f) => f.key)).toEqual(["a", "c"]);
  });
});

describe("factorValue", () => {
  it("gives a number with its unit", () => {
    expect(factorValue(factor({ value: 30, unit: "m" }), 3)).toBe("30 m");
  });
  it("gives text as sent", () => {
    expect(factorValue(factor({ value: "D" }), 3)).toBe("D");
  });
  it("says not reported for an absent value, never zero", () => {
    expect(factorValue(factor({ value: null, reason: "no tool reported it" }), 3)).toBe("not reported");
  });
  it("shows a real zero as zero", () => {
    expect(factorValue(factor({ value: 0, unit: "kg/yr" }), 3)).toBe("0 kg/yr");
  });
});

describe("scenarioFor, stackNumber and ranking", () => {
  const withStack = scenario({ factors: [factor({ key: "stack_number", value: 2 })] });
  it("finds the scenario of a pathway and quantity", () => {
    const f = facility({ scenarios: [withStack] });
    expect(scenarioFor(f, "community_inhalation", "hq")).toBe(withStack);
    expect(scenarioFor(f, "community_inhalation", "cancer_risk")).toBeNull();
    expect(scenarioFor(f, "worker_inhalation", "hq")).toBeNull();
  });
  it("reads the stack a scenario names", () => {
    expect(stackNumber(withStack)).toBe(2);
    expect(stackNumber(scenario())).toBeNull();
  });
  it("ranks facilities highest first and skips those without the scenario", () => {
    const list = [
      facility({ frs_id: "A", scenarios: [scenario({ value: 1 })] }),
      facility({ frs_id: "B", scenarios: [scenario({ value: 5 })] }),
      facility({ frs_id: "C", scenarios: [] }),
    ];
    expect(ranking(list, "community_inhalation", "hq").map((r) => r.frsId)).toEqual(["B", "A"]);
  });
});
