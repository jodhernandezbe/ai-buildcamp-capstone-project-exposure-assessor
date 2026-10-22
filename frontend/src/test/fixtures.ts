import { EMPTY_WORKSPACE } from "../hooks/useWorkspaceStore";
import type { Extremum, Facility, WorkspaceState } from "../types/workspace";

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
    medium: "AIR STACK",
    reporting_year: 2020,
    total_release: 100,
    release_unit: "Pounds",
    emission_rate_g_s: 1,
    operating_hours_per_year: 8760,
    operating_hours_source: null,
    conditions_of_use: [],
    lifecycle_stages: [],
    conditions_note: null,
    industry: null,
    stacks: [],
    receptors: null,
    meteorology: null,
    exposure: null,
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
