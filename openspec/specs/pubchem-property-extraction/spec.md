# pubchem-property-extraction Specification

## Purpose
Reads the configured physical-chemical fields from a PubChem record as numbers with units, using only statements that are clear and consistent, so they can be converted and validated like any other source.

## Requirements

### Requirement: Fields come from configuration
The system SHALL extract exactly the fields named in the PubChem configuration, each with the record heading to read and the unit the value must convert to. Adding a field to the configuration SHALL make it extractable with no code change. Initially the fields are molecular weight, vapor pressure and density.

#### Scenario: Configured fields
- **WHEN** the record has data under the configured headings of the three fields
- **THEN** a candidate value is read for each

#### Scenario: Unconfigured data ignored
- **WHEN** the record has data under other headings
- **THEN** it is not returned

#### Scenario: New field
- **WHEN** a field entry is added to the configuration
- **THEN** it is extracted on the next parse with no code change

### Requirement: Use only clear statements
The system SHALL accept a statement only when it gives exactly one number and one unit, the number is finite and greater than zero, and the unit converts to the field's target unit. A structured number-and-unit entry SHALL be preferred to text. Ranges, inequalities (`>`, `<`), several numbers, estimates, and statements with no or an unconvertible unit (a specific gravity, for example) SHALL be skipped with a reason. A statement that names a temperature SHALL be accepted only if the temperature is inside the configured range for that field.

#### Scenario: Clear statement
- **WHEN** a statement reads like `1 mmHg at 25 °C` (placeholder values)
- **THEN** the value and the unit are read

#### Scenario: Range
- **WHEN** a statement gives `1-2 mmHg`
- **THEN** it is skipped

#### Scenario: Inequality
- **WHEN** a statement gives `> 1 mmHg`
- **THEN** it is skipped

#### Scenario: Dimensionless
- **WHEN** a density heading holds a specific gravity with no unit
- **THEN** it is skipped

#### Scenario: Wrong temperature
- **WHEN** a vapor pressure statement is at a temperature outside the configured range
- **THEN** it is skipped

#### Scenario: Structured entry
- **WHEN** an entry carries a number and a unit as separate fields
- **THEN** they are used instead of reading the text

### Requirement: Several statements must agree
When several clear statements exist for a field, the system SHALL return the median only if all of them lie within the configured ratio of each other; otherwise it SHALL return no value with a reason. It SHALL NOT pick one of conflicting statements.

#### Scenario: Agreeing statements
- **WHEN** the clear statements are within the configured ratio
- **THEN** their median is returned

#### Scenario: Conflicting statements
- **WHEN** two clear statements differ by more than the ratio
- **THEN** no value is returned and the reason says the statements conflict

#### Scenario: One statement
- **WHEN** only one clear statement exists
- **THEN** its value is returned

### Requirement: Tolerate the shape of the record
The system SHALL treat the record as untrusted: find sections by heading wherever nested under the expected parents, ignore entries of an unexpected type, and never raise on a missing or malformed part.

#### Scenario: Empty or unrelated record
- **WHEN** the record is empty, not an object, or has no `Section` list
- **THEN** no values are returned, a reason is given per field, and nothing is raised

#### Scenario: Wrong types
- **WHEN** a heading, string, number or list has an unexpected type (null, boolean, number for text)
- **THEN** that entry is ignored
