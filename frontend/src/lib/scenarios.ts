import type { Facility, ScenarioFactor, WorstCaseScenario } from "../types/workspace";
import { formatNumber, formatWithUnit, NOT_REPORTED } from "./format";

/** The groups of a scenario's factors, in the order they are told: from the source to the receptor. */
export const FACTOR_GROUPS: { key: ScenarioFactor["group"]; title: string }[] = [
  { key: "source", title: "Source" },
  { key: "release", title: "Release" },
  { key: "conditions", title: "Conditions" },
  { key: "receptor_model", title: "Receptor model" },
];

export interface FactorGroup {
  key: ScenarioFactor["group"];
  title: string;
  factors: ScenarioFactor[];
}

/** The factors by group, in the told order; a group with no factor is left out. */
export function groupFactors(factors: ScenarioFactor[]): FactorGroup[] {
  return FACTOR_GROUPS.map(({ key, title }) => ({ key, title, factors: factors.filter((f) => f.group === key) })).filter(
    (group) => group.factors.length > 0,
  );
}

/** A factor's value as shown: a number with its unit, text as given, "not reported" when absent. */
export function factorValue(factor: ScenarioFactor, digits: number): string {
  const { value, unit } = factor;
  if (value === null || value === undefined) return NOT_REPORTED;
  if (typeof value === "string") return value;
  return unit ? formatWithUnit(value, unit, digits) : formatNumber(value, digits);
}

/** The facility's scenario of a pathway and quantity; null when it has none. */
export function scenarioFor(facility: Facility, pathwayKey: string, quantity: string): WorstCaseScenario | null {
  return facility.scenarios.find((s) => s.pathway_key === pathwayKey && s.quantity === quantity) ?? null;
}

/** The stack a community scenario names (the "stack_number" factor); null when it names none. */
export function stackNumber(scenario: WorstCaseScenario): number | null {
  const value = scenario.factors.find((f) => f.key === "stack_number")?.value;
  return typeof value === "number" ? value : null;
}

export interface Ranked {
  frsId: string;
  name: string | null;
  value: number;
}

/** The facilities that have a scenario of a pathway and quantity, highest value first. */
export function ranking(facilities: Facility[], pathwayKey: string, quantity: string): Ranked[] {
  return facilities
    .flatMap((facility) => {
      const scenario = scenarioFor(facility, pathwayKey, quantity);
      return scenario ? [{ frsId: facility.frs_id, name: facility.name, value: scenario.value }] : [];
    })
    .sort((a, b) => b.value - a.value);
}
