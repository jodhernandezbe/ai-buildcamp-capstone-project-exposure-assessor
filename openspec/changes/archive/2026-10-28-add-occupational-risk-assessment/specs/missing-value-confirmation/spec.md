## MODIFIED Requirements

### Requirement: Ask before concluding when a needed value is missing
The system SHALL stop the turn and ask the user when a value the requested analysis needs is
missing and the missing value changes the result, and for the properties the properties tool
lists as missing (the benchmarks, the occupational limit, the molecular weight, the vapor
pressure and the density), including those that no equation uses, which then say so in their
purpose. The request SHALL list every such value in
one confirmation request, and each entry SHALL say which field is missing, the chemical or
facility it belongs to, and what it is used for.

#### Scenario: Missing chemical property blocks a risk result
- **WHEN** the requested risk result needs an inhalation reference concentration for a chemical and CompTox and PubChem both have none
- **THEN** the turn ends with a confirmation request naming the chemical, the missing RfC and why it is needed, and no risk figure is reported for it

#### Scenario: Missing value that does not change the result is not asked
- **WHEN** a value is missing that the result does not use and the properties tool does not list as one that can be entered
- **THEN** no confirmation request is made for it

#### Scenario: One request per turn
- **WHEN** several values are missing in the same analysis
- **THEN** they appear in a single confirmation request, not one request per value

## ADDED Requirements

### Requirement: Properties of the worker screening can be asked for
When no source has them, the properties tool SHALL list as missing, with their accepted units, plausible range and purpose, the 8-hour occupational limit (mg/m³ or µg/m³), the molecular weight (g/mol), the vapor pressure and the density, beside the benchmarks it already lists. The purpose of a value that no equation uses (vapor pressure, density) SHALL say so. A value the user enters SHALL be checked like any entered value (finite, an accepted unit, inside the range), used as given, labelled "user-provided" and never replace a value a source has; a value the user declines SHALL not be asked again in the thread.

#### Scenario: Nothing has the value
- **WHEN** no source has the occupational limit
- **THEN** it is listed as missing with its units, range and purpose

#### Scenario: A source has it
- **WHEN** PubChem lists an 8-hour limit
- **THEN** the limit is not listed and an entered one is ignored

#### Scenario: Entered limit
- **WHEN** the user enters 3.2 mg/m³ for the occupational limit
- **THEN** the properties report that limit with the source "user-provided" and the worker screening uses it

#### Scenario: Out of range
- **WHEN** the user enters a negative limit
- **THEN** it is rejected with the reason and the limit stays missing

#### Scenario: Not used in an equation
- **WHEN** the vapor pressure or the density is listed
- **THEN** its purpose says it is not used in an equation

### Requirement: An entered molecular weight reaches the limits
A molecular weight the user enters when no source has one SHALL be used to convert the occupational limits that PubChem gives in ppm, before they are read, so the limit and its source are those of the converted value. A molecular weight a source has SHALL be used instead.

#### Scenario: Weight enables a ppm limit
- **WHEN** CompTox has no molecular weight, the user enters one and PubChem gives a limit in ppm
- **THEN** the limit is converted with the entered weight

#### Scenario: Source weight wins
- **WHEN** a source has a molecular weight and the user also entered one
- **THEN** the source's weight converts the limit
