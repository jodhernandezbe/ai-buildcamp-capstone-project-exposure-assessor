/* Generated from api/schemas/ by npm run gen:types. Do not edit. */

/**
 * Any one event of the stream (used to export the event union).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "StreamEventSchema".
 */
export type StreamEventSchema =
  | TurnStarted
  | ScopeDecision
  | GuardrailPivotResponse
  | ToolStatus
  | WorkspaceUpdate
  | Token
  | AssistantMessage
  | Usage
  | ErrorEvent
  | TurnFinished;

export interface ApiContract {
  ChatRequest: ChatRequest;
  ClientConfig: ClientConfig;
  KeyStatusResponse: KeyStatusResponse;
  KeyUpdatePayload: KeyUpdatePayload;
  KeysStatusResponse: KeysStatusResponse;
  StreamEventSchema: StreamEventSchema;
  UsageTotals: UsageTotals;
  WorkspaceState: WorkspaceState;
}
/**
 * Body of ``POST /api/v1/chat/stream``.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ChatRequest".
 */
export interface ChatRequest {
  message: string;
  thread_id: string;
}
/**
 * Display settings the frontend needs (``GET /api/v1/settings/client``).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ClientConfig".
 */
export interface ClientConfig {
  map: MapConfig;
  /**
   * Chat model that drives the agent.
   */
  model: string;
  narrow_breakpoint_px: number;
  significant_digits: number;
  suggestions: string[];
  thresholds: Thresholds;
}
/**
 * Basemap style URLs and the marker radii (px) for the smallest and largest emission rate.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "MapConfig".
 */
export interface MapConfig {
  dark_style: string;
  initial_view: InitialView;
  light_style: string;
  marker_max_px: number;
  marker_min_px: number;
}
/**
 * What the map shows before any facility.
 */
export interface InitialView {
  east: number;
  north: number;
  south: number;
  west: number;
}
/**
 * Status thresholds (unitless HQ and lifetime cancer risk).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Thresholds".
 */
export interface Thresholds {
  cancer_lower: number;
  cancer_upper: number;
  hq_concern: number;
  hq_near_lower: number;
}
/**
 * Whether a key is stored; never the key or any part of it.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "KeyStatusResponse".
 */
export interface KeyStatusResponse {
  configured: boolean;
}
/**
 * Body of ``POST /api/v1/settings/openai-key``; the key is never echoed or logged.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "KeyUpdatePayload".
 */
export interface KeyUpdatePayload {
  /**
   * OpenAI API key to store in the OS keychain.
   */
  api_key: string;
}
/**
 * The status of every key the interface stores, in one response.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "KeysStatusResponse".
 */
export interface KeysStatusResponse {
  census: KeyStatusResponse;
  comptox: KeyStatusResponse;
  openai: KeyStatusResponse;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "TurnStarted".
 */
export interface TurnStarted {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  thread_id: string;
  turn_id: string;
  type: "turn_started";
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ScopeDecision".
 */
export interface ScopeDecision {
  in_scope: boolean;
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  type: "scope";
}
/**
 * The in-character redirect sent instead of running the agent on an off-topic turn.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "GuardrailPivotResponse".
 */
export interface GuardrailPivotResponse {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  text: string;
  type: "guardrail_pivot";
}
/**
 * A tool step: ``started`` carries the label; ``finished`` adds the outcome.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ToolStatus".
 */
export interface ToolStatus {
  call_id: string;
  label: string;
  phase: "started" | "finished";
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  status: ("ok" | "error") | null;
  tool_name: string;
  type: "tool_status";
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "WorkspaceUpdate".
 */
export interface WorkspaceUpdate {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  state: WorkspaceState;
  type: "workspace_update";
}
/**
 * The current workspace of one thread.
 *
 * Attributes:
 *     framing_version: Increases only when the set of placed facilities or buffers changes.
 *     bounds: Extent of the placed facilities and buffers; None when none is placed.
 *     facilities: One per FRS ID, in the order first reported.
 *     selected_frs_id: Facility whose receptors the ribbon shows (the highest risk, or the
 *         only one); None when no single facility stands out.
 *     chemical: The queried chemical and its provenance.
 *     risk: Highest risk values across the attributed facilities.
 *     receptors: Receptors of the selected facility.
 *     meteorology: Meteorology of the selected facility, else the latest result.
 *     unattributed: Results not attached to any facility.
 *     warnings: Results left out (malformed, unattributable) and why.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "WorkspaceState".
 */
export interface WorkspaceState {
  bounds: BoundingBox | null;
  chemical: Chemical;
  facilities: Facility[];
  framing_version: number;
  meteorology: Meteorology | null;
  receptors: Receptors | null;
  risk: RiskSummary;
  selected_frs_id: string | null;
  unattributed: Unattributed[];
  warnings: string[];
}
/**
 * Extent of the placed facilities and buffers, decimal degrees (WGS84).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "BoundingBox".
 */
export interface BoundingBox {
  east: number;
  north: number;
  south: number;
  west: number;
}
/**
 * The chemical as queried, with its properties and read-across provenance.
 *
 * Attributes:
 *     cas_number: CAS number as queried.
 *     molecular_weight_g_mol: Molecular weight, g/mol.
 *     rfc_mg_m3: Inhalation reference concentration, mg/m³.
 *     iur_per_ug_m3: Inhalation unit risk, (µg/m³)⁻¹.
 *     sources: Field name -> source the value came from.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Chemical".
 */
export interface Chemical {
  cas_number: string | null;
  iur_per_ug_m3: number | null;
  molecular_weight_g_mol: number | null;
  read_across: ReadAcross;
  rfc_mg_m3: number | null;
  sources: {
    [k: string]: string;
  };
  warnings: string[];
}
/**
 * The read-across outcome for the queried chemical (surrogate values are scores 0-1).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ReadAcross".
 */
export interface ReadAcross {
  cosine_similarity: number | null;
  hybrid_score: number | null;
  kind: "not_evaluated" | "direct_tri_match" | "read_across" | "unresolved";
  surrogate_cas: string | null;
  surrogate_name: string | null;
  tanimoto_similarity: number | null;
  warnings: string[];
  within_applicability_domain: boolean | null;
}
/**
 * One facility of the emissions inventory with what the other tools reported about it.
 *
 * Attributes:
 *     doc_ctrl_num: TRI document control number (the inventory has no TRI facility ID).
 *     total_release: Annual quantity in ``release_unit``, as reported.
 *     emission_rate_g_s: Total release averaged over ``operating_hours_per_year``.
 *     stack_source: Where the NEI stack lookup came from, when one was made for the facility.
 *     status: Worst-case risk status; None while no risk is computed.
 *     buffer: The receptor radius drawn as a circle around the facility, when receptors exist.
 *     sector: Schematic downwind sector (toward ``wind_toward_deg``, length the receptor radius);
 *         never a modelled plume footprint. Present with both receptors and meteorology.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Facility".
 */
export interface Facility {
  address: string | null;
  buffer: Polygon | null;
  cas_number: string | null;
  city: string | null;
  county: string | null;
  doc_ctrl_num: string | null;
  emission_rate_g_s: number;
  exposure: ExposureRanges | null;
  frs_id: string;
  industry: Industry | null;
  latitude: number;
  longitude: number;
  medium: string;
  meteorology: Meteorology | null;
  name: string | null;
  operating_hours_per_year: number;
  receptors: Receptors | null;
  release_unit: string;
  reporting_year: number;
  sector: Polygon | null;
  stacks: Stack[];
  state: string | null;
  status: ("below" | "near" | "above") | null;
  total_release: number;
  zip_code: string | null;
}
/**
 * A GeoJSON polygon: one closed ring of ``[longitude, latitude]`` positions (WGS84).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Polygon".
 */
export interface Polygon {
  coordinates: number[][][];
  type: "Polygon";
}
/**
 * Ranges over the evaluated stacks of one facility; None when no stack has the quantity.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ExposureRanges".
 */
export interface ExposureRanges {
  cancer_risk_representative: Extreme | null;
  cancer_risk_worst: Extreme | null;
  concentration_representative: Extreme | null;
  concentration_worst: Extreme | null;
  hq_representative: Extreme | null;
  hq_worst: Extreme | null;
  stacks_evaluated: number;
  stacks_given: number;
  warnings: string[];
}
/**
 * The lowest and highest value of one quantity over a facility's stacks.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Extreme".
 */
export interface Extreme {
  high: number;
  high_stack: number;
  low: number;
  low_stack: number;
}
/**
 * Primary industry of the TRI submission; origin is reported, assigned or None.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Industry".
 */
export interface Industry {
  code_origin: string | null;
  naics_code: string | null;
  naics_title: string | null;
  source: string | null;
}
/**
 * Annual representative conditions at a point: m/s, degrees clockwise from north, K.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Meteorology".
 */
export interface Meteorology {
  ambient_temperature_k: number;
  screening_default: boolean;
  source: string;
  stability_class: string;
  warnings: string[];
  /**
   * Direction the wind blows from.
   */
  wind_from_deg: number;
  wind_speed_m_s: number;
  /**
   * Downwind direction, ``(from + 180) % 360``.
   */
  wind_toward_deg: number;
}
/**
 * Residents within ``radius_km`` of a point; ``age_distribution`` is percent per band.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Receptors".
 */
export interface Receptors {
  age_distribution: {
    [k: string]: number;
  };
  radius_km: number;
  screening_default: boolean;
  source: string;
  total_population: number;
  warnings: string[];
}
/**
 * One release point with its provenance tier and, when computed, its results.
 *
 * Attributes:
 *     stack_number: 1-based position in the exposure call that evaluated it, else None.
 *     tier: 1 Empirical NEI, 2 PSTK by SCC, 3 EPA global default; None without a source.
 *     tier_label: ``Tier 1: Empirical NEI`` and so on.
 *     scc: SCC behind a PSTK stack, when reported.
 *     scc_description: Most specific process description of that SCC, from an SCC lookup
 *         in the same thread; None when no lookup returned it.
 *     scc_score: Match score (0-1) of that lookup.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Stack".
 */
export interface Stack {
  diameter_m: number | null;
  exit_temperature_k: number | null;
  exit_velocity_m_s: number | null;
  height_m: number | null;
  representative: Scenario | null;
  scc: string | null;
  scc_description: string | null;
  scc_score: number | null;
  source: string | null;
  stack_number: number | null;
  tier: (1 | 2 | 3) | null;
  tier_label: string | null;
  warnings: string[];
  worst_case: Scenario | null;
}
/**
 * Screening result for one set of weather: concentration µg/m³, HQ and cancer risk unitless.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Scenario".
 */
export interface Scenario {
  cancer_risk: number | null;
  /**
   * Downwind distance of the maximum.
   */
  distance_m: number | null;
  hq: number | null;
  max_concentration_ug_m3: number | null;
}
/**
 * Highest worst-case and representative HQ and cancer risk; ``reason`` when none exists.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "RiskSummary".
 */
export interface RiskSummary {
  cancer_risk_representative: Extremum | null;
  cancer_risk_worst: Extremum | null;
  hq_representative: Extremum | null;
  hq_worst: Extremum | null;
  /**
   * Why no value yet, e.g. not computed.
   */
  reason: string | null;
}
/**
 * The highest value of one risk quantity over every attributed facility.
 *
 * Attributes:
 *     value: The value (HQ and cancer risk are unitless).
 *     frs_id: Facility whose stack gave it.
 *     facility_name: That facility's name, as reported.
 *     stack_number: The stack that gave it.
 *     status: Position against the configured thresholds of concern.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Extremum".
 */
export interface Extremum {
  facility_name: string | null;
  frs_id: string;
  stack_number: number;
  status: "below" | "near" | "above";
  value: number;
}
/**
 * A result that could not be tied to exactly one facility, and why.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Unattributed".
 */
export interface Unattributed {
  reason: string;
  tool: string;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Token".
 */
export interface Token {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  text: string;
  type: "token";
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "AssistantMessage".
 */
export interface AssistantMessage {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  text: string;
  type: "assistant_message";
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Usage".
 */
export interface Usage {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  session: UsageTotals;
  turn: UsageTotals;
  type: "usage";
}
/**
 * Token counts and estimated cost (USD) of a turn or a session.
 *
 * ``cost_status`` is ``estimate`` when every call was priced, ``lower_bound`` when some call
 * reported no usage, and ``unpriced`` (``cost_usd`` null) when the model has no price.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "UsageTotals".
 */
export interface UsageTotals {
  cached_input_tokens: number;
  calls: number;
  complete: boolean;
  cost_status: "estimate" | "lower_bound" | "unpriced";
  cost_usd: number | null;
  input_tokens: number;
  output_tokens: number;
  priced_on: string | null;
}
/**
 * A user-safe message and the id under which the details were logged.
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ErrorEvent".
 */
export interface ErrorEvent {
  correlation_id: string;
  message: string;
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  type: "error";
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "TurnFinished".
 */
export interface TurnFinished {
  /**
   * Position of the event in its stream, from 0.
   */
  seq: number;
  type: "turn_finished";
}
/**
 * A box on the map, decimal degrees (WGS84, west negative).
 *
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "InitialView".
 */
export interface InitialView1 {
  east: number;
  north: number;
  south: number;
  west: number;
}
