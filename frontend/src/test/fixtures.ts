import { EMPTY_WORKSPACE } from "../hooks/useWorkspaceStore";
import type { Extremum, Facility, WorkspaceState, WorstCaseScenario } from "../types/workspace";

/** Synthetic values (round numbers), never real measurements. */
export function extremum(value: number, status: Extremum["status"], stack = 1): Extremum {
  return { value, status, frs_id: "F1", facility_name: "Plant F1", stack_number: stack };
}

export function facility(over: Partial<Facility> = {}): Facility {
  return {
    frs_id: "F1",
    name: "Plant F1",
    address: "1 Test Road",
    city: "Testville",
    county: "Test",
    state: "TX",
    zip_code: "00000",
    latitude: 10,
    longitude: -20,
    cas_number: "1-1-1",
    doc_ctrl_num: "DOC1",
    naics_subsector: null,
    naics_subsector_title: null,
    medium: "AIR STACK",
    reporting_year: 2020,
    total_release: 100,
    release_unit: "Pounds",
    emission_rate_g_s: 1,
    operating_hours_per_year: 8760,
    operating_hours_source: null,
    fugitive_release_kg_per_year: null,
    fugitive_reporting_year: null,
    conditions_of_use: [],
    lifecycle_stages: [],
    conditions_note: null,
    industry: null,
    stacks: [],
    receptors: null,
    meteorology: null,
    exposure: null,
    occupational_exposure: null,
    operational_profile: null,
    scenarios: [],
    exposure_graph: null,
    status: null,
    screening: null,
    buffer: null,
    sector: null,
    ...over,
  };
}

export function workspace(over: Partial<WorkspaceState> = {}): WorkspaceState {
  return { ...EMPTY_WORKSPACE, ...over };
}

/** A worker screening with synthetic round numbers. */
export function worker(over: Partial<NonNullable<Facility["occupational_exposure"]>> = {}) {
  const tier = {
    label: "Baseline manufacturing ventilation",
    ventilation_m3_per_s: 1.4,
    mixing_factor: 0.5,
    workplace_concentration_mg_m3: 2,
    twa_mg_m3: 2,
    oel_ratio: 0.4,
    hq: 0.2,
    cancer_risk: 3e-6,
    risk_tier: "elevated" as const,
  };
  return {
    fugitive_release_kg_per_year: 1000,
    fugitive_reporting_year: 2020,
    operating_days_per_year: 250,
    hours_per_day: 16,
    oel_twa_mg_m3: 5,
    oel_source: "OSHA PEL-TWA (PubChem)",
    rfc: 1,
    iur: 1e-6,
    vapor_pressure_mmhg: null,
    vapor_pressure_source: null,
    baseline: tier,
    worst_case: { ...tier, label: "Worst case, enclosed zone", risk_tier: "exceedance" as const },
    risk_tier: "elevated" as const,
    assumptions: ["a well-mixed zone"],
    warnings: ["no IUR"],
    ...over,
  };
}

/** An operational profile with synthetic round numbers. */
export function profile(over: Partial<NonNullable<Facility["operational_profile"]>> = {}) {
  return {
    naics_code: "325199",
    life_cycle_stage: ["Processing"],
    cou_category: ["Processing as a reactant"],
    cdr_sector: {
      code: "IS21",
      name: "All Other Basic Organic Chemical Manufacturing",
      matched_naics_prefix: "32519",
      naics_edition: "2007",
    },
    days_per_week: 5,
    operating_days_per_year: 250,
    hours_per_day: 16,
    annual_operating_hours: 4240,
    schedule_source: "Census QPC test",
    warnings: [],
    ...over,
  };
}

/** A worst-case scenario with synthetic round numbers. */
export const scenario = (over: Partial<WorstCaseScenario> = {}): WorstCaseScenario => ({
  pathway_key: "community_inhalation",
  pathway: "Outdoor Air → Inhalation → General Population",
  quantity: "hq",
  quantity_label: "Hazard quotient",
  value: 2,
  tier: "at or above threshold",
  benchmark: 0.1,
  factors: [],
  receptors: [],
  receptors_note: null,
  notes: [],
  ...over,
});
