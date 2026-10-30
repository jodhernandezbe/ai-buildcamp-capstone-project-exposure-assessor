## ADDED Requirements

### Requirement: Fugitive air release on the record
The system SHALL also read the TRI `AIR FUG` medium (a configured medium, one more query like the stack one, with the same year window, paging, throttling and validation) and put each facility's latest-year fugitive release, converted to kg/yr with the shared unit conversion, on its record as `fugitive_release_kg_per_year`, null when TRI has none. Fugitive rows SHALL NOT become separate facilities, SHALL NOT enter the stack emission rate, and a facility with only a fugitive release SHALL NOT be listed as a stack source.

#### Scenario: Both media
- **WHEN** a facility reports stack and fugitive air in the latest year
- **THEN** its record has the stack release as before and its fugitive release in kg/yr

#### Scenario: Stack only
- **WHEN** a facility has no fugitive row
- **THEN** the fugitive release is null

#### Scenario: Fugitive only
- **WHEN** a facility has a fugitive row but no stack row
- **THEN** it is not returned as a stack source

#### Scenario: Stack numbers unchanged
- **WHEN** the fugitive medium is added
- **THEN** every stack release and emission rate equals what it was

#### Scenario: Unconvertible unit
- **WHEN** a fugitive row's unit is not a mass
- **THEN** that release is null and a warning counts it

## MODIFIED Requirements

### Requirement: Emission rate from annual release
The system SHALL convert each annual release to an emission rate in g/s by converting the quantity to grams with the shared unit conversion and dividing by the operating seconds per year. The operating hours per year SHALL be those of the facility's industry from the Census plant-hours baseline, matched on the facility's NAICS code (most specific prefix first), and otherwise the configured default (default 8,760, continuous operation); the choice SHALL be made through a single dedicated function, and the hours and their source SHALL be reported on each record, with these hours (`operating_hours_per_year`) being the facility's annual operating hours. A row whose unit cannot be converted to grams SHALL be discarded with a counted warning, never passed through unconverted.

#### Scenario: Pounds per year to g/s
- **WHEN** a facility reports 8,760 pounds in a year, has no baseline match, and the default operating hours are 8,760
- **THEN** the emission rate is 8,760 pounds in grams divided by 31,536,000 s (about 0.126 g/s)

#### Scenario: Industry hours
- **WHEN** a facility's NAICS code matches a baseline row of 84 hours per week
- **THEN** its operating hours are 4,380 per year, its emission rate is its annual release divided by 4,380 hours in seconds, and its source names the QPC release and matched code

#### Scenario: Facility without a match
- **WHEN** a facility has no NAICS code or no baseline row matches it
- **THEN** its operating hours are the configured default and its source says so

#### Scenario: Two facilities, two hours
- **WHEN** one lookup returns a facility with a baseline match and one without
- **THEN** each record carries its own operating hours and source

#### Scenario: Configured hours
- **WHEN** the configured operating hours per year are changed
- **THEN** the emission rate and the reported hours of facilities without a baseline match change with no code change

#### Scenario: Unconvertible unit
- **WHEN** a row's unit is unknown or not a mass
- **THEN** the row is not returned and a warning counts it

#### Scenario: Invalid hours
- **WHEN** the configured default operating hours are zero, negative, above the number of hours in a year, or non-numeric
- **THEN** the settings loader raises a `ValueError` and no lookup is made
