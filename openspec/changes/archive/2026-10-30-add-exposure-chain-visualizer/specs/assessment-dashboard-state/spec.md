## ADDED Requirements

### Requirement: Each facility carries its exposure graph
The state SHALL carry, for each facility, an exposure graph: lanes (one per pathway, with whether it is
available and why not, and its status), nodes (source facility, each evaluated stack, the pathway, the
route, each receptor group and the endpoint) and edges (each with the quantity it carries). Every
quantity SHALL carry its value as the tools reported it, its unit and its source, or no value and a
reason; no value SHALL be computed, converted or estimated to build the graph. Fixed text and units SHALL
come from configuration. The graph SHALL be sent in `workspace_update` and described in the generated
schema and types.

#### Scenario: Community branches
- **WHEN** a facility has two evaluated stacks and residents in four age bands
- **THEN** its graph has two stack nodes feeding the outdoor air and four age-band receptor nodes, each with its dose

#### Scenario: Worker lane
- **WHEN** a facility has an occupational result
- **THEN** the worker lane carries the fugitive release, the worst-case and baseline concentrations, the TWA, the limit and its source, the ratio and the tier

#### Scenario: Unavailable lane
- **WHEN** a facility has no occupational result
- **THEN** the worker lane is marked unavailable with the configured reason and has no nodes

#### Scenario: Absent quantity
- **WHEN** a tool did not report a value (for example no cancer risk)
- **THEN** that quantity has no value and carries the reason, and the rest of the graph is unchanged

#### Scenario: Contract
- **WHEN** the schema is exported
- **THEN** the TypeScript types include the graph and the contract check passes
