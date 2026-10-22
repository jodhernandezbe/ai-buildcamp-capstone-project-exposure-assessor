## MODIFIED Requirements

### Requirement: NEI stack candidates by FRS ID
The system SHALL provide a tool that, given an EPA Facility Registry Service identifier and, optionally, the facility's EIS IDs as the emissions inventory listed them, returns candidate stacks for that facility: each candidate has stack height (m), stack diameter (m), exit velocity (m/s) and exit temperature (K) from the NEI, converted from the units the table reports. When EIS IDs are given (digit strings; others are ignored), their rows SHALL be read from the local NEI table and no request SHALL be made; otherwise the facility's EIS IDs SHALL be found with the FRS-to-EIS lookup. Each candidate SHALL identify NEI as its source. The tool SHALL call only the Envirofacts FRS query and no other network service.

#### Scenario: One stack
- **WHEN** the facility's EIS ID has one valid stack in the table
- **THEN** one candidate is returned in m, m, m/s and K with source "NEI", and no warnings

#### Scenario: EIS IDs given
- **WHEN** the call carries the facility's EIS IDs
- **THEN** the candidates are those IDs' rows and no request is made

#### Scenario: Unit conversion
- **WHEN** the table reports height and diameter in feet, velocity in ft/s and temperature in degrees Fahrenheit
- **THEN** the returned values equal the converted SI values

#### Scenario: Facility without an EIS ID
- **WHEN** no EIS IDs are given and the FRS lookup finds none, or fails
- **THEN** no candidates are returned and a warning states why and that the SCC-based tier 2 tool can be used

#### Scenario: EIS ID absent from the table
- **WHEN** none of the facility's EIS IDs has a row in the table
- **THEN** no candidates are returned and a warning says the facility has no NEI stack data

#### Scenario: Blank FRS ID
- **WHEN** the FRS ID is empty, whitespace or not digits, and no EIS IDs are given
- **THEN** no candidates are returned with a warning, and no request is made
