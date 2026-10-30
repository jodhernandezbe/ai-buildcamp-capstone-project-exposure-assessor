## ADDED Requirements

### Requirement: Occupational exposure and operational profile on each facility
The state SHALL carry, for each facility, the `occupational_exposure` and `operational_profile` exactly as the assessment tool returned them (the TWA, benchmark and its source, limit ratio, hazard quotient, cancer risk, tier, warnings; the NAICS code, life cycle stages, condition-of-use categories, CDR sector, operating days, hours per day and annual operating hours), each absent (null) with its reason when the tool did not report it, under the same fail-closed rules as the other values. They SHALL be sent in the `workspace_update` event and described in the generated schema and TypeScript types.

#### Scenario: Values come from the tool
- **WHEN** the assessment reports a TWA for a facility
- **THEN** the facility's state shows that value and its source

#### Scenario: Non-finite value
- **WHEN** a result contains a non-finite or boolean number
- **THEN** that value is left out with a warning and the rest of the facility is kept

#### Scenario: Not reported
- **WHEN** the tool reported no occupational result for a facility
- **THEN** the fields are null with a reason and the facility's community values are unaffected

#### Scenario: Contract
- **WHEN** the schema is generated
- **THEN** the TypeScript types include the two new objects and the contract test passes

### Requirement: Highest worker values across facilities
The state SHALL carry a worker risk summary with the highest limit ratio, worker hazard quotient and worker cancer risk over the assessed facilities, for the baseline and the enclosed-zone tiers, each naming the facility it comes from and that facility's tier; each is a selection among the values the tools returned, never a sum, mean or conversion. When no facility has a worker result the summary SHALL be empty with a reason.

#### Scenario: Highest value
- **WHEN** two facilities have worker results
- **THEN** each figure of the summary is the larger of the two and names its facility

#### Scenario: Nothing yet
- **WHEN** no facility has a worker result
- **THEN** every figure is absent and a reason is given
