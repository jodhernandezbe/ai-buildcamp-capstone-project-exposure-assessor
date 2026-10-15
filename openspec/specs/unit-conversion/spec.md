# unit-conversion Specification

## Purpose
Guarantees that numeric values reach the risk calculations in a known unit, by converting each reported value to a target unit and refusing values whose units are unknown or dimensionally incompatible.

## Requirements

### Requirement: Convert to the target unit
The system SHALL convert a numeric value from its reported unit to a requested target unit.

#### Scenario: Compatible units
- **WHEN** a value in "ug/m^3" is converted to "mg/m^3"
- **THEN** the result is the value divided by 1000, in "mg/m^3"

#### Scenario: Same unit
- **WHEN** the reported unit equals the target unit
- **THEN** the value is returned unchanged

#### Scenario: Reciprocal units
- **WHEN** a value in "(ug/m^3)^-1" is converted to "(mg/m^3)^-1"
- **THEN** the result is the value multiplied by 1000

### Requirement: Reject incompatible or unknown units
The system SHALL signal a conversion failure, and SHALL NOT return the unconverted number, when the reported unit cannot be parsed or its dimensionality differs from the target's.

#### Scenario: Dimension mismatch
- **WHEN** a value in "g/cm^3" is converted to "mmHg"
- **THEN** the conversion fails with an error naming both units

#### Scenario: Unknown unit
- **WHEN** the reported unit is not recognized
- **THEN** the conversion fails with an error naming the unit

#### Scenario: Non-finite value
- **WHEN** the value is NaN or infinite
- **THEN** the conversion fails

### Requirement: Configurable unit spellings
The system SHALL apply the configured alias table to a reported unit before parsing it, so that source spellings such as "mg/m3" resolve to a parsable unit without code changes.

#### Scenario: Alias applied
- **WHEN** the alias table maps "mg/m3" to "mg/m^3" and a value in "mg/m3" is converted to "ug/m^3"
- **THEN** the conversion succeeds

#### Scenario: Alias added later
- **WHEN** a new spelling is added to the alias table
- **THEN** values reported with that spelling convert with no code change

#### Scenario: Alias on the target
- **WHEN** the target unit itself appears in the alias table
- **THEN** it is resolved the same way as a reported unit
