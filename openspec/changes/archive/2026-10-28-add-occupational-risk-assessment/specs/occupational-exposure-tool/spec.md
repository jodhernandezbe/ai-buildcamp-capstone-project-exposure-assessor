## Purpose

Screens worker exposure at each assessed facility by joining its fugitive release, its operating schedule, the occupational limit and the toxicity values through the occupational model, with every assumption stated.

## ADDED Requirements

### Requirement: Occupational result for each assessed facility
The system SHALL provide, for each facility the assessment evaluates, an `occupational_exposure` result with the inputs used (fugitive release in kg/yr, operating days per year and hours per day, the benchmark and its source, RfC and IUR), for both ventilation tiers the workplace concentration, the 8-hour TWA, the limit ratio, the worker hazard quotient, the worker cancer risk and the risk tier, and the warnings. The ambient result SHALL NOT change.

#### Scenario: Both tiers
- **WHEN** a facility has a fugitive release, a schedule and a limit
- **THEN** the result holds the baseline and worst-case values, and the worst-case concentration is the higher

#### Scenario: Ambient unchanged
- **WHEN** the occupational result is added
- **THEN** the community concentration, hazard quotient and cancer risk equal what they were before

### Requirement: Fail closed on missing inputs
The system SHALL return null for every quantity that needs an input it does not have, with a warning naming it: no fugitive release (TRI reports none or the facility is absent from that medium) gives null concentrations, never zero; no benchmark gives a null ratio; no RfC or IUR gives a null hazard quotient or cancer risk. A zero reported fugitive release SHALL give a zero concentration and "acceptable" only when a benchmark exists to compare.

#### Scenario: No fugitive release
- **WHEN** the facility has no AIR FUG row
- **THEN** the occupational concentrations and tier are null and the warning says TRI reports no fugitive release

#### Scenario: No benchmark
- **WHEN** PubChem gave no TWA limit
- **THEN** the ratio is null, the hazard quotient and cancer risk are still computed, and the warning says the limit is missing

#### Scenario: Reported zero
- **WHEN** the fugitive release is 0 kg/yr and a limit exists
- **THEN** the concentrations are 0 and the tier is "acceptable"

### Requirement: Assumptions are visible
The result SHALL state that the box model treats the fugitive release as generated only during operating hours inside one well-mixed zone, that the two ventilation tiers are screening defaults and not the plant's, that the exposure is not an OSHA compliance determination, and the source of the schedule.

#### Scenario: Statement present
- **WHEN** an occupational result is returned
- **THEN** its warnings or assumptions carry those statements

### Requirement: Volatility context from the chemical's vapor pressure
The system SHALL report the chemical's vapor pressure in mmHg at about 25 degC with its source (CompTox, or PubChem when CompTox has none, by the existing source order) beside the occupational result, taken from the properties already resolved for the chemical and never looked up again per facility. When the vapor pressure is at or below the configured threshold the result SHALL carry a warning that a large fugitive release into workplace air is less plausible for so non-volatile a chemical. The vapor pressure SHALL NOT change any concentration, ratio, dose, risk or tier. A missing vapor pressure SHALL give a null value with its reason and no volatility warning, never a default.

#### Scenario: Volatile chemical
- **WHEN** the vapor pressure is above the threshold
- **THEN** it is reported with its source and no volatility warning is added

#### Scenario: Non-volatile chemical
- **WHEN** the vapor pressure is at or below the threshold
- **THEN** the warning is added and the tier equals what it would be without it

#### Scenario: CompTox lacks it
- **WHEN** CompTox has no vapor pressure and PubChem has a clear one
- **THEN** the PubChem value is reported and its source says PubChem

#### Scenario: Neither source has it
- **WHEN** no source has a usable vapor pressure
- **THEN** the value is null with the reason and no volatility warning is added

#### Scenario: Configured threshold
- **WHEN** the threshold in the configuration is changed
- **THEN** which chemicals get the warning changes with no code change

### Requirement: The assistant is told how to read it
The description of the assessment tool SHALL say what the occupational result is, that it is a worker screening distinct from the community result, how the tiers read, that vapor pressure is context and not an input, and that a null must be reported as not computed.

#### Scenario: Description
- **WHEN** the tool description is read
- **THEN** it covers those points and names no call order
