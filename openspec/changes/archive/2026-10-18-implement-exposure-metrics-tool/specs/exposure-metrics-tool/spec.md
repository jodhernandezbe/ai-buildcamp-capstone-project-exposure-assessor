## Purpose

The last step of an assessment: turns an emission rate, a stack, the weather, the population and the toxicity values into a screening concentration, a dose and risks, with the assumptions made visible.

## ADDED Requirements

### Requirement: Screening concentration by the EPA procedure
The system SHALL provide a tool that, given an emission rate (g/s), one stack (height, diameter, exit velocity, exit temperature), the meteorology result, the population result and the toxicity values, returns the maximum ground-level centerline concentration of the source in micrograms per cubic meter, found as EPA's SCREEN3 screening model does with its full meteorology and automated distance array: over every configured combination of stability class and 10 m wind speed and every configured distance (flat terrain, rural dispersion, receptor at the configured height), with the plume rise and the wind adjusted to the stack height. The result SHALL state the distance, stability class, 10 m wind speed and effective release height at which the maximum occurs, and the 1-hour and the annual-average concentration (the 1-hour maximum times the configured annual factor).

#### Scenario: Worst case over the grid
- **WHEN** a valid source is evaluated
- **THEN** the returned maximum is the largest concentration over all weather combinations and distances, with the combination and the distance that produced it

#### Scenario: Annual average
- **WHEN** the 1-hour maximum is 100 micrograms per cubic meter and the configured annual factor is 0.08
- **THEN** the annual-average concentration is 8 micrograms per cubic meter

#### Scenario: Taller stack
- **WHEN** only the stack height is raised
- **THEN** the maximum concentration does not increase

#### Scenario: Doubled emission
- **WHEN** the emission rate is doubled
- **THEN** every concentration is doubled

#### Scenario: Maximum at the edge of the range
- **WHEN** the worst case is at the last distance of the array
- **THEN** a warning says the true maximum may lie farther away

### Requirement: Representative-conditions scenario
The system SHALL also report the concentration for the representative conditions given in the meteorology input (its wind speed, stability class and ambient temperature), maximized over the same distances, so that the typical-year result can be read beside the worst case. The ambient temperature of the meteorology input SHALL be used for the plume rise in both scenarios.

#### Scenario: Typical year below the worst case
- **WHEN** the representative conditions are among the grid combinations
- **THEN** the representative maximum does not exceed the screening maximum

#### Scenario: Ambient temperature
- **WHEN** the ambient temperature is raised and the stack gas temperature is unchanged
- **THEN** the buoyant plume rise does not increase

### Requirement: Hazard quotient and cancer risk
The system SHALL return the hazard quotient (annual exposure concentration against the RfC) and the lifetime excess cancer risk (lifetime exposure concentration against the IUR) for both scenarios, using the configured exposure time, frequency, duration and averaging time. A missing or non-positive RfC SHALL make the hazard quotient null with a warning, and a missing or negative IUR SHALL make the cancer risk null with a warning; neither SHALL be guessed.

#### Scenario: Both values present
- **WHEN** the RfC and the IUR are given
- **THEN** the hazard quotient and the cancer risk are returned

#### Scenario: No IUR
- **WHEN** the IUR is null
- **THEN** the cancer risk is null, the hazard quotient is still returned, and a warning says the IUR was not available

#### Scenario: No RfC
- **WHEN** the RfC is null
- **THEN** the hazard quotient is null with a warning, and the cancer risk is still returned

### Requirement: Dose per age band
The system SHALL return the average daily dose in milligrams per kilogram per day for each age band that has a non-zero share of the population, using that band's configured inhalation rate and body weight, and SHALL name the band with the highest dose. When the population result is the screening default or has no residents it SHALL still compute the bands present and say so in a warning.

#### Scenario: Children present
- **WHEN** the age distribution has non-zero shares for 0-4 and 18-64
- **THEN** doses are returned for both bands and the highest is named

#### Scenario: Band absent
- **WHEN** a band's share is zero
- **THEN** no dose is reported for it

### Requirement: Null results with warnings, never defaults
The system SHALL validate its inputs and, when a required value is missing, not finite, not positive where it must be, or outside what the model supports (for example a stack without all four values, a non-positive emission rate, an unknown stability class), SHALL return null for the affected results and a warning naming the problem, and SHALL NOT substitute default values or raise for data problems. A stack with any null value (for example from an empty NEI result) SHALL give null concentrations and a warning to use the tier-2 stack tool. An emission rate of zero SHALL give zero concentrations, not an error.

#### Scenario: Stack with a missing value
- **WHEN** the exit temperature is null
- **THEN** the concentrations, hazard quotient and cancer risk are null and the warning names the missing value

#### Scenario: Non-positive emission rate
- **WHEN** the emission rate is negative
- **THEN** all results are null with a warning

#### Scenario: Zero emission rate
- **WHEN** the emission rate is zero
- **THEN** the concentrations are zero and the hazard quotient and cancer risk are zero

### Requirement: Assumptions reported with the result
The result SHALL carry warnings that always state the method's limits relevant to the result (the screening maximum may be at a distance where nobody lives; the screening default status of the meteorology or population input when their `source` says so), so the agent can pass them on.

#### Scenario: Default population
- **WHEN** the population result's source is "screening default"
- **THEN** a warning says the age mix is generic

#### Scenario: Default meteorology
- **WHEN** the meteorology result's source is "screening default"
- **THEN** a warning says the representative scenario uses generic weather

### Requirement: Tool description sets expectations
The tool's description, as seen by the LLM, SHALL state the method (EPA SCREEN3 procedure, flat terrain, no building downwash, no mixing-height limit), the units of every output, that it evaluates one stack so it is called once per stack candidate and the results reported as a range, that the headline is a worst case, what a null result means, and that the results are screening estimates, not regulatory determinations.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the inputs, the units of each output, the method's limits and the one-call-per-candidate rule
