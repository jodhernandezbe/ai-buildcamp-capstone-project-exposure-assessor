## Purpose

Lets the user decide what happens when a chemical property or stack parameter the assessment
needs cannot be found: proceed without it, or supply the value with its unit so the analysis
uses it. Nothing missing is ever guessed, and every supplied value is labelled as user-provided.

## ADDED Requirements

### Requirement: Ask before concluding when a needed value is missing
The system SHALL stop the turn and ask the user when a value the requested analysis needs is
missing and the missing value changes the result. The request SHALL list every such value in
one confirmation request, and each entry SHALL say which field is missing, the chemical or
facility it belongs to, and what it is used for.

#### Scenario: Missing chemical property blocks a risk result
- **WHEN** the requested risk result needs an inhalation reference concentration for a chemical and CompTox and PubChem both have none
- **THEN** the turn ends with a confirmation request naming the chemical, the missing RfC and why it is needed, and no risk figure is reported for it

#### Scenario: Missing value that does not change the result is not asked
- **WHEN** a property is missing but the requested result does not use it
- **THEN** no confirmation request is made for that property

#### Scenario: One request per turn
- **WHEN** several values are missing in the same analysis
- **THEN** they appear in a single confirmation request, not one request per value

### Requirement: Two answers per missing value
Each entry in a confirmation request SHALL accept exactly one of two answers: proceed without
the value, or enter a value with a unit. The unit selector SHALL offer only units of the same
physical quantity, and the field's documented target unit SHALL be visible on the entry.

#### Scenario: Proceed without the value
- **WHEN** the user confirms an entry as proceed without
- **THEN** the value stays absent, the warning that explains its absence is kept, and no substitute value is used

#### Scenario: Enter a value in another unit
- **WHEN** the user enters a vapor pressure of 760 torr
- **THEN** the system converts it to the documented target unit, mmHg, before the analysis uses it

#### Scenario: Entry in a unit of another quantity
- **WHEN** a request for a stack height arrives with a unit of pressure
- **THEN** the request is rejected with a reason and the entry is asked again

### Requirement: Validate entered values and never coerce them
The system SHALL accept an entered value only when it is a finite number, converts exactly to
the target unit, and lies inside the plausible range configured for its quantity. A value
that fails any check SHALL be rejected with a reason and asked again. A value SHALL NOT be
clipped to the range, rounded into it, or replaced with a default.

#### Scenario: Value outside the plausible range
- **WHEN** the user enters a stack height of 4500 m
- **THEN** the entry is rejected with the accepted range and asked again

#### Scenario: Value that is not a number
- **WHEN** the entry is empty, text, infinite or a boolean
- **THEN** the entry is rejected with a reason and asked again

#### Scenario: Temperature entered in Celsius
- **WHEN** the user enters an exit temperature of 25 degC for a stack
- **THEN** the value is converted as a temperature (298.15 K), not as a difference, and checked against the plausible range for exit temperature

#### Scenario: Reciprocal unit
- **WHEN** an inhalation unit risk of 0.002 (mg/m3)^-1 is entered
- **THEN** it is converted to 2e-6 (ug/m3)^-1, the configured target unit, before the analysis uses it; the number is not used unchanged

### Requirement: Entered values are used and labelled
A value the user enters SHALL be used by the analysis in place of the missing one, and every
place that reports the source of that value SHALL report it as user-provided. The reported
value SHALL carry the unit it was converted to.

#### Scenario: Supplied vapor pressure is used
- **WHEN** the user supplies a vapor pressure for a chemical that had none
- **THEN** the analysis uses it and the chemical's reported source for vapor pressure is user-provided

#### Scenario: Supplied stack diameter is used
- **WHEN** the user supplies a stack diameter for a facility whose stack has none
- **THEN** the stack's reported source is user-provided and the stack is assessed with that diameter

### Requirement: The pending request belongs to its thread
A confirmation request SHALL stay open in its chat thread until it is answered. Answers SHALL
apply only to the thread they were given in. If the user sends a new message without answering
an open request, each open entry SHALL be treated as proceed without, and the agent SHALL say so.

#### Scenario: Open request survives a reload
- **WHEN** the user reloads the page while a confirmation request is open
- **THEN** the same request is shown again in that thread, with its entries unanswered

#### Scenario: New message ignores the request
- **WHEN** the user sends a new question instead of answering the request
- **THEN** the open entries are treated as proceed without, the agent reports that it did so, and it answers the new question

### Requirement: Declining or ignoring never invents a result
A result computed without a value the user declined to supply SHALL report the value as absent
with its reason, and SHALL NOT present a number for the affected risk as if it were complete.

#### Scenario: Risk without a declined RfC
- **WHEN** the user proceeds without an RfC and no IUR is available
- **THEN** the hazard quotient and cancer risk for that chemical are reported as not computed, with the reason
