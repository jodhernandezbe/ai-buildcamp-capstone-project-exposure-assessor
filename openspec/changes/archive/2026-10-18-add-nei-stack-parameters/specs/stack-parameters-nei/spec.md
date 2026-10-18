## Purpose

Tier 1 source of stack geometry and exit conditions: gives the agent the facility's own stack combinations from the EPA National Emissions Inventory, looked up by FRS ID.

## ADDED Requirements

### Requirement: NEI stack candidates by FRS ID
The system SHALL provide a tool that, given an EPA Facility Registry Service identifier, returns candidate stacks for that facility: each candidate has stack height (m), stack diameter (m), exit velocity (m/s) and exit temperature (K) from the NEI, converted from the units the table reports. The facility's EIS IDs SHALL be found with the FRS-to-EIS lookup and their rows read from the local NEI table. Each candidate SHALL identify NEI as its source. The tool SHALL call only the Envirofacts FRS query and no other network service.

#### Scenario: One stack
- **WHEN** the facility's EIS ID has one valid stack in the table
- **THEN** one candidate is returned in m, m, m/s and K with source "NEI", and no warnings

#### Scenario: Unit conversion
- **WHEN** the table reports height and diameter in feet, velocity in ft/s and temperature in degrees Fahrenheit
- **THEN** the returned values equal the converted SI values

#### Scenario: Facility without an EIS ID
- **WHEN** the FRS lookup finds no EIS ID, or fails
- **THEN** no candidates are returned and a warning states why and that the SCC-based tier 2 tool can be used

#### Scenario: EIS ID absent from the table
- **WHEN** none of the facility's EIS IDs has a row in the table
- **THEN** no candidates are returned and a warning says the facility has no NEI stack data

#### Scenario: Blank FRS ID
- **WHEN** the FRS ID is empty, whitespace or not digits
- **THEN** no candidates are returned with a warning, and no request is made

### Requirement: Distinct candidates without mixing
The system SHALL return the distinct combinations of the four values found for the facility, not one chosen stack and not an average. Rows with equal values SHALL collapse to one candidate, and combinations that are equal after rounding each value to the configured number of significant digits SHALL be merged, keeping the first row's actual values. Values SHALL NOT be combined or altered across release points.

#### Scenario: Repeated release points
- **WHEN** two release points have identical values
- **THEN** one candidate is returned

#### Scenario: Near-identical stacks
- **WHEN** two stacks differ only below the configured significant digits
- **THEN** they are merged into one candidate whose values are those of one real row

#### Scenario: Several EIS IDs
- **WHEN** the facility has two EIS IDs, both with stacks
- **THEN** the candidates of both are returned together

### Requirement: Bounded, ordered candidate list
The system SHALL order candidates by stack height, lowest first (ties by exit velocity, exit temperature, then diameter, each lowest first), return at most the configured number, and report in a warning how many distinct combinations existed, how many were merged and how many were omitted.

#### Scenario: More candidates than the cap
- **WHEN** the facility has more distinct combinations than the configured maximum
- **THEN** the lowest stacks up to the maximum are returned, in order, with a warning giving the total and the number omitted

### Requirement: Fail closed on implausible NEI values
The system SHALL treat a value as missing when it is not a finite number, is a boolean, is not positive, or lies outside the configured plausible range for that quantity. A row with any missing value SHALL NOT become a candidate; values SHALL NOT be repaired, clipped or filled from another row.

#### Scenario: Non-numeric or blank value
- **WHEN** a row has a blank or non-numeric stack height
- **THEN** that row is not a candidate

#### Scenario: Out-of-range value
- **WHEN** a row's exit temperature is above the configured maximum
- **THEN** that row is not a candidate

#### Scenario: Every row invalid
- **WHEN** all of the facility's rows are invalid
- **THEN** no candidates are returned and a warning gives the number of rows rejected

### Requirement: Tool description orders the tiers and the scenarios
The NEI tool's description, as seen by the LLM, SHALL state that it is the first choice for stack parameters, that it returns several candidate stacks which should each be evaluated with the exposure calculation and reported as a range, and that the SCC-based tool is to be used only when it returns no candidates.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the input, the units of each output, the candidate semantics and the fallback to the SCC-based tool
