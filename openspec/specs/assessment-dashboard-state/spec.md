# assessment-dashboard-state Specification

## Purpose

Turns the agent's tool calls and results into the typed state shown on the left pane, so the
dashboard reflects exactly what the tools reported and never shows a number no tool produced.

## Requirements

### Requirement: State derived only from tool calls and results
The dashboard state of a thread SHALL be rebuilt after every finished tool call from that
thread's tool-call arguments and tool results alone. It SHALL NOT parse assistant prose, SHALL
NOT compute, estimate or convert scientific values itself (beyond selecting maxima the tools
already returned), and SHALL carry, for each value, the tool `source` and warnings that came
with it. A field no tool reported SHALL be absent (null) with a reason; the UI renders it as
"not reported".

#### Scenario: Values come from tools
- **WHEN** the meteorology tool returns a wind speed of `w` m/s
- **THEN** the dashboard meteorology shows `w` with that result's `source` and warnings

#### Scenario: Not yet evaluated
- **WHEN** no read-across tool call has been made in the thread
- **THEN** the chemical provenance is marked "not evaluated" rather than "direct TRI match"

### Requirement: Untrusted results fail closed
A tool result that is not valid JSON, has the wrong shape, contains non-finite numbers or a
boolean where a number is expected, or has coordinates outside -90..90 / -180..180, SHALL be
left out of the dashboard with a warning; it SHALL NOT break the stream or the rest of the
state. A tool that returned an error SHALL contribute nothing.

#### Scenario: Malformed result
- **WHEN** a tool result is not JSON
- **THEN** that result is skipped, a dashboard warning is added and the turn continues

#### Scenario: Bad coordinates
- **WHEN** an inventory record has latitude 123
- **THEN** that facility is not placed on the map and a warning names its FRS ID

### Requirement: Facilities
The state SHALL list one facility per FRS ID from the emissions inventory results (latest
result wins; the complete list the tool returns beside the text the model reads, falling back to the
facilities in that text), with name, address fields, coordinates, TRI document control number, reported
release and its unit, emission rate (g/s), assumed operating hours (h/yr), medium, reporting
year, the NAICS subsector code and title the inventory reported for it, the TSCA conditions of use and life cycle stages the inventory reported for it (with the
note when there are none), and the queried CAS number. It SHALL attach, by matching identifiers only:
- industry (NAICS code, title, origin) from the industry tool, matched by document control number;
- stack candidates and their source from the NEI stack tool, matched by FRS ID;
- receptors (population, age distribution, radius used, source) from the population tool,
  matched by coordinates equal to the facility's within a configured tolerance;
- exposure results (per-stack results and ranges) from the exposure tool, matched by an
  emission rate equal to exactly one facility's emission rate.
A result that matches no facility, or more than one, SHALL NOT be attached to any facility and
SHALL be reported as an unattributed result.

#### Scenario: Stacks attached
- **WHEN** the NEI stack tool is called with a facility's FRS ID
- **THEN** that facility shows its candidates with source NEI

#### Scenario: Ambiguous exposure result
- **WHEN** two facilities share the emission rate passed to the exposure tool
- **THEN** the exposure result is attached to neither and is listed as unattributed

#### Scenario: Conditions of use carried
- **WHEN** the inventory record has two conditions of use and two life cycle stages
- **THEN** the facility shows both, unchanged, and no condition is derived by the workspace

#### Scenario: Older state without conditions
- **WHEN** a record has no conditions fields
- **THEN** the facility has empty lists and no note, and the state still builds

#### Scenario: Subsector carried
- **WHEN** the inventory record has subsector "325" with a title
- **THEN** the facility shows both unchanged, and a record without them gives nulls

### Requirement: Stack provenance tier
Each stack shown SHALL carry a provenance tier derived only from its reported source: Tier 1
"Empirical NEI" for NEI, Tier 2 "PSTK by SCC" for PSTK (with the SCC, and its description and
match score when an SCC lookup in the same thread returned that SCC), and Tier 3 "EPA global
default" for the global default. A stack with no source SHALL have no tier.

#### Scenario: Generic stack
- **WHEN** a stack's source is the AirToxScreen global default
- **THEN** its tier is "Tier 3: EPA global default"

#### Scenario: PSTK with lookup
- **WHEN** a PSTK stack's SCC was returned by an SCC lookup in the same thread
- **THEN** the tier shows that SCC's description and score

### Requirement: Executive summary
The state SHALL expose a summary of:
- the highest worst-case and representative hazard quotient and lifetime cancer risk across
  attributed facility ranges, each with the facility and stack that gave it, and a status of
  `below`, `near` or `above` the threshold of concern (HQ thresholds and cancer-risk thresholds
  from configuration);
- the chemical: CAS number as queried, molecular weight, inhalation RfC and IUR from the
  chemical properties tool with their sources, and the read-across outcome (direct TRI match,
  read-across surrogate with surrogate CAS, name, cosine, Tanimoto, hybrid score and
  applicability-domain flag, or unresolved);
- receptors: the population, radius and age distribution of the selected facility (the highest
  risk one, or the only one);
- meteorology: wind speed, direction (from), ambient temperature, stability class and source, with the
  point it is for and the facility at that point (none when the point is not one of the facilities).

#### Scenario: Status above concern
- **WHEN** the highest worst-case HQ exceeds the configured threshold of concern
- **THEN** the HQ status is `above`

#### Scenario: Surrogate out of domain
- **WHEN** the read-across result has `within_applicability_domain` false
- **THEN** the provenance shows the surrogate scores flagged as outside the applicability domain

#### Scenario: No exposure yet
- **WHEN** no exposure tool has returned
- **THEN** HQ and cancer risk are absent with reason "not yet computed"

### Requirement: Map framing hints
The state SHALL include the bounding box of all placed facilities and a monotonically increasing
version that changes only when the set of placed facilities or receptor buffers changes, so the
map moves the camera only on real changes.

#### Scenario: New facilities found
- **WHEN** an inventory result adds facilities
- **THEN** the bounding box covers them and the framing version increases

#### Scenario: Unrelated update
- **WHEN** only a chemical properties result arrives
- **THEN** the framing version does not change

### Requirement: Batch results attach by FRS ID
Each facility of a batch assessment SHALL be placed on the map from its record and given its stacks (with their tier and SCC), weather, residents and exposure, attached by FRS ID, so facilities with the same emission rate keep their own results. A later single-tool result for a facility SHALL replace the batch one. An invalid facility item SHALL be left out with a warning; a batch result without its details SHALL be skipped with a warning.

#### Scenario: Same emission rate
- **WHEN** two assessed facilities have the same emission rate
- **THEN** each shows its own stacks and risk

#### Scenario: Later single result
- **WHEN** an exposure result for one facility follows the batch result
- **THEN** that facility shows the later result

### Requirement: Screening shown per facility
Each facility of a batch assessment SHALL carry its screening outcome: fully assessed, worst case only, screened out at the bound or with its own stacks, or not assessed, with the bound HQ and cancer risk and the reason. A screened-out facility SHALL be placed on the map from its record even when the inventory was not listed. The facility card SHALL say why a facility has no stacks or risk (screened out, with its bound and the threshold; or not assessed, with the reason the assessment gave; or not covered by a batch assessment yet) instead of implying the values are missing, and SHALL say when only the worst case was computed. A not-assessed result SHALL NOT replace a facility's real result, and one for an FRS ID with no placed facility SHALL be ignored.

#### Scenario: Screened-out facility
- **WHEN** a facility was screened out at the bound
- **THEN** its card shows the bound HQ, the threshold and that it was screened out, not "not reported"

#### Scenario: Worst case only
- **WHEN** a facility kept only its own-stack worst case
- **THEN** its card shows its stacks and worst-case risk and says the representative case, weather and residents were not computed

#### Scenario: Not assessed with a reason
- **WHEN** the batch assessment returns a facility as not assessed with a reason
- **THEN** its card says "Not assessed" and the reason, not that stack parameters were not obtained

#### Scenario: Not covered yet
- **WHEN** a facility is on the map from the inventory but no batch assessment has covered it
- **THEN** its card says that no batch assessment has covered it yet

### Requirement: The chemical carries its name
The workspace's chemical SHALL carry the preferred name the properties result gave (None when it gave none), with its source among the chemical's sources, taken only from that result.

#### Scenario: Name reported
- **WHEN** a properties result with a preferred name is projected
- **THEN** the chemical shows that name and its source

#### Scenario: Name absent
- **WHEN** the properties result has no name
- **THEN** the chemical's name is None and nothing else fills it
