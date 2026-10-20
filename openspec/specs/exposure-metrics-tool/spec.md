# exposure-metrics-tool Specification

## Purpose

The last step of an assessment: turns an emission rate, a stack, the weather, the population and the toxicity values into a screening concentration, a dose and risks, with the assumptions made visible.

## Requirements

### Requirement: Screening concentration by the EPA procedure
The system SHALL provide a tool that, given an emission rate (g/s), a list of candidate stacks (each with height, diameter, exit velocity, exit temperature), the meteorology result, the population result and the toxicity values, returns for EACH stack the maximum ground-level centerline concentration of the source in micrograms per cubic meter, found as EPA's SCREEN3 screening model does with its full meteorology and automated distance array: over every configured combination of stability class and 10 m wind speed and every configured distance (flat terrain, rural dispersion, receptor at the configured height), with the plume rise and the wind adjusted to the stack height. Each per-stack result SHALL state the distance, stability class, 10 m wind speed and effective release height at which the maximum occurs, and the 1-hour and the annual-average concentration (the 1-hour maximum times the configured annual factor). The per-stack results SHALL be returned in the order the stacks were given, each numbered from 1.

#### Scenario: Worst case over the grid
- **WHEN** a valid stack is evaluated
- **THEN** its returned maximum is the largest concentration over all weather combinations and distances, with the combination and the distance that produced it

#### Scenario: Annual average
- **WHEN** the 1-hour maximum is 100 micrograms per cubic meter and the configured annual factor is 0.08
- **THEN** the annual-average concentration is 8 micrograms per cubic meter

#### Scenario: Taller stack
- **WHEN** two stacks differ only in height
- **THEN** the taller stack's maximum concentration is not higher

#### Scenario: Doubled emission
- **WHEN** the emission rate is doubled
- **THEN** every concentration of every stack is doubled

#### Scenario: Maximum at the edge of the range
- **WHEN** a stack's worst case is at the last distance of the array
- **THEN** that stack's warnings say the true maximum may lie farther away

#### Scenario: Several stacks in one call
- **WHEN** ten candidate stacks are given
- **THEN** ten per-stack results are returned, each equal to what evaluating that stack alone would give

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
The system SHALL validate its inputs and, when a required value is missing, not finite, not positive where it must be, or outside what the model supports (for example a stack without all four values, a non-positive emission rate, an unknown stability class), SHALL return null for the affected results and a warning naming the problem, and SHALL NOT substitute default values or raise for data problems. A stack with any null value (for example from an empty NEI result) SHALL give null concentrations for that stack and a warning to use the tier-2 stack tool, and SHALL NOT prevent the other stacks from being evaluated. An empty list of stacks SHALL give no per-stack results, a null range and a warning. An emission rate of zero SHALL give zero concentrations, not an error.

#### Scenario: Stack with a missing value
- **WHEN** one of three stacks has a null exit temperature
- **THEN** that stack's concentrations, hazard quotient and cancer risk are null with a warning naming the missing value, and the other two stacks have results

#### Scenario: No stacks
- **WHEN** the list of stacks is empty
- **THEN** there are no per-stack results, the range is null and a warning says no stack was given

#### Scenario: Non-positive emission rate
- **WHEN** the emission rate is negative
- **THEN** all results of every stack are null with a warning

#### Scenario: Zero emission rate
- **WHEN** the emission rate is zero
- **THEN** the concentrations are zero and the hazard quotient and cancer risk are zero

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

### Requirement: Tool description sets expectations
The tool's description, as seen by the LLM, SHALL state the method (EPA SCREEN3 procedure, flat terrain, no building downwash, no mixing-height limit), the units of every output, that it evaluates every stack given in one call so ALL of a facility's candidate stacks are passed together (never a subset, never one call per stack) and the returned range is what to report, that the headline is a worst case, what a null result means, and that the results are screening estimates, not regulatory determinations.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the inputs, the units of each output, the method's limits and the all-candidates-in-one-call rule

### Requirement: Range over the stacks
The result SHALL carry, beside the per-stack results, the range over the stacks that could be evaluated: for the annual-average concentration, the hazard quotient and the cancer risk, in both the worst case and the representative case, the lowest and the highest value and the number (from 1) of the stack giving each; the count of stacks given and of stacks evaluated; and facility-level warnings that say how many stacks could not be evaluated. A quantity that is null for every stack SHALL have a null range entry.

#### Scenario: Range over three stacks
- **WHEN** three stacks give hazard quotients of 0.2, 0.5 and 0.1
- **THEN** the range reports 0.1 as the lowest (stack 3) and 0.5 as the highest (stack 2)

#### Scenario: One stack could not be evaluated
- **WHEN** one of three stacks has a null value
- **THEN** the range is over the two evaluated stacks, the counts say 3 given and 2 evaluated, and a warning says one stack could not be evaluated

#### Scenario: Representative case ranged too
- **WHEN** several stacks are evaluated
- **THEN** the range gives the lowest and highest representative-weather concentration, hazard quotient and cancer risk with their stacks, beside the worst-case ones

#### Scenario: No cancer risk
- **WHEN** the IUR is null
- **THEN** the cancer-risk range is null while the concentration and hazard-quotient ranges are reported
