## Purpose

Tier 1 source of stack geometry and exit conditions: gives the agent facility-specific release-point parameters from the EPA National Emissions Inventory, looked up by FRS ID.

## ADDED Requirements

### Requirement: NEI stack lookup by FRS ID
The system SHALL provide a tool that, given an EPA Facility Registry Service identifier, returns stack height (m), stack diameter (m), exit velocity (m/s) and exit temperature (K) for that facility from a bundled NEI point-source release-point file. Values SHALL be converted from the units the file reports them in to these units. The result SHALL identify NEI as its source. The tool SHALL NOT call a network service.

#### Scenario: Facility present with one release point
- **WHEN** the tool is called with an FRS ID that has one release point in the NEI file with all four values present and plausible
- **THEN** it returns the four values in m, m, m/s and K, with source "NEI" and no warnings

#### Scenario: Unit conversion
- **WHEN** the file reports height and diameter in feet, velocity in ft/s and temperature in degrees Fahrenheit
- **THEN** the returned values equal the converted SI values

#### Scenario: Facility absent
- **WHEN** the FRS ID is not in the NEI file
- **THEN** all four values are absent (None), and a warning states the facility was not found in the NEI and that the SCC-based tier 2 tool can be used

#### Scenario: Blank FRS ID
- **WHEN** the FRS ID is empty or whitespace
- **THEN** all four values are None with a warning, and the file is not searched

### Requirement: Several release points per facility
When a facility has several release points, the system SHALL return the parameters of a single, deterministically chosen release point (the tallest stack among those with all four values valid) and SHALL report in a warning how many release points were found and which rule chose the returned one.

#### Scenario: Two stacks
- **WHEN** the facility has two release points of 20 m and 35 m, both complete
- **THEN** the 35 m release point's values are returned, with a warning naming 2 release points and the tallest-stack rule

#### Scenario: Tallest stack incomplete
- **WHEN** the tallest release point lacks exit temperature and a shorter one is complete
- **THEN** the shorter, complete release point is returned

### Requirement: Fail closed on implausible NEI values
The system SHALL treat a value as missing when it is not a finite number, is a boolean, is not positive, or lies outside the configured plausible range for that quantity. A release point with any missing value SHALL NOT be returned; values SHALL NOT be mixed across release points or guessed.

#### Scenario: Non-numeric value
- **WHEN** the only release point has stack height "N/A"
- **THEN** all four values are None and a warning names the invalid field

#### Scenario: Out-of-range value
- **WHEN** the only release point has exit temperature below the configured minimum
- **THEN** all four values are None and a warning names the out-of-range field

### Requirement: Tool description orders the tiers
The NEI tool's description, as seen by the LLM, SHALL state that it is the first choice for stack parameters and that the SCC-based tool is to be used only when it returns no values.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the inputs, the units of each output, and directs the reader to the SCC-based tool when no values are returned
