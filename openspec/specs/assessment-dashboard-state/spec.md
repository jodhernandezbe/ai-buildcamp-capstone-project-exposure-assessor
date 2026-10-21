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
year and the queried CAS number. It SHALL attach, by matching identifiers only:
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
- meteorology: wind speed, direction (from), ambient temperature, stability class and source.

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
