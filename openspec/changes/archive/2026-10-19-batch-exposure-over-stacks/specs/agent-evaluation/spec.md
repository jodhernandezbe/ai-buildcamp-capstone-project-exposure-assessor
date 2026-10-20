## MODIFIED Requirements

### Requirement: Deterministic checks score tool use and completion
Each scenario SHALL declare deterministic checks evaluated on its record by the evaluation
framework, each yielding pass or fail with a reason: which tools must, must not, or may be
called; how many times a tool is called relative to the tool outputs (for example once per
assessed facility); which arguments a call must carry (for example the CAS number asked for, or
every stack candidate a facility's stack result returned); call order where it matters; that no
call was unrecorded; and that the run completed. Checks SHALL compare against values found in
the record's tool outputs, never against numbers written into the check.

#### Scenario: Forbidden tool called
- **WHEN** a scenario forbids a tool and the record contains a call to it
- **THEN** that check fails and names the call

#### Scenario: Count tied to tool output
- **WHEN** a check requires one exposure calculation per assessed facility
- **THEN** the expected facilities are taken from the stack requests in the record, and a different number of exposure calls for a facility fails

#### Scenario: Arguments tied to tool output
- **WHEN** a check requires the exposure calculation to carry every NEI candidate of a facility
- **THEN** the expected candidates are taken from the stack result in the record, and a call missing any of them fails

### Requirement: Full assessment of a facility with its own stacks
The catalogue SHALL include a scenario asking for an assessment of a chemical given by CAS number
whose recorded inventory returns facilities that have NEI stack candidates. It SHALL pass only
when: the run completed with no unrecorded call; the chemical's properties and the emissions
inventory were requested with the CAS number asked for; every facility the agent assessed had
its NEI stacks requested with its `frs_id`, its weather and its population requested with that
facility's coordinates; the exposure calculation ran exactly once per assessed facility, carrying
every NEI stack candidate of that facility and its emission rate; the industry, SCC process and
SCC stack tools were not called for a facility that had NEI candidates; and a judge confirms the
report gives a summary, a per-facility table with units showing the range over stacks and both
the worst and the representative case, the source of each input, and a limitations section.

#### Scenario: One stack evaluated out of several
- **WHEN** a facility has several NEI candidates and the exposure call for it carries only one
- **THEN** the candidate-coverage check fails naming the missing candidates

#### Scenario: Some candidates left out
- **WHEN** a facility has ten NEI candidates and the exposure call for it carries six
- **THEN** the candidate-coverage check fails naming the missing candidates

#### Scenario: One call per stack
- **WHEN** the agent runs the exposure calculation once per candidate instead of once per facility
- **THEN** the one-call-per-facility check fails

#### Scenario: Unneeded fallback
- **WHEN** a facility has NEI candidates and the agent also calls the SCC stack tool for it
- **THEN** the forbidden-tool check fails

#### Scenario: Complete assessment
- **WHEN** the agent follows the chain for every facility it assesses and writes the full report
- **THEN** every check passes
