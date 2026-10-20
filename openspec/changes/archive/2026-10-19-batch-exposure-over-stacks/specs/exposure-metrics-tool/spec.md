## MODIFIED Requirements

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

### Requirement: Tool description sets expectations
The tool's description, as seen by the LLM, SHALL state the method (EPA SCREEN3 procedure, flat terrain, no building downwash, no mixing-height limit), the units of every output, that it evaluates every stack given in one call so ALL of a facility's candidate stacks are passed together (never a subset, never one call per stack) and the returned range is what to report, that the headline is a worst case, what a null result means, and that the results are screening estimates, not regulatory determinations.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the inputs, the units of each output, the method's limits and the all-candidates-in-one-call rule

## ADDED Requirements

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
