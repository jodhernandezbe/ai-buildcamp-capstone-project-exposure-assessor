## MODIFIED Requirements

### Requirement: Assumptions reported with the result
The result SHALL carry warnings that always state the method's limits relevant to the result (the screening maximum may be at a distance where nobody lives; the screening default status of the meteorology or population input when their `source` says so), so the agent can pass them on. The result SHALL echo the stack's `source` as `stack_source`, even when the numbers are null, and SHALL warn when the stack is the EPA global default (not the facility's own; short, cold and slow, so concentrations are far higher than for a real stack) or a process default by SCC.

#### Scenario: Default population
- **WHEN** the population result's source is "screening default"
- **THEN** a warning says the age mix is generic

#### Scenario: Default meteorology
- **WHEN** the meteorology result's source is "screening default"
- **THEN** a warning says the representative scenario uses generic weather

#### Scenario: Global default stack
- **WHEN** the stack's source is "AirToxScreen global default"
- **THEN** `stack_source` has that value and a warning says the stack is the EPA global default, not this facility's own

#### Scenario: Process default stack
- **WHEN** the stack's source is "PSTK"
- **THEN** a warning says it is the default for this kind of process, not the facility's own

#### Scenario: Facility's own stack
- **WHEN** the stack's source is "NEI"
- **THEN** no generic-stack warning is added

#### Scenario: Source kept when nothing is computed
- **WHEN** a stack value is missing so the numbers are null
- **THEN** `stack_source` still carries the stack's source
