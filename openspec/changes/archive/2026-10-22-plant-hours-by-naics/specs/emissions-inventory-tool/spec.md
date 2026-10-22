## MODIFIED Requirements

### Requirement: Returned facility record
Each returned record SHALL contain the facility FRS ID, facility name, environmental medium, reporting year, the TRI submission control number (`doc_ctrl_num`, null if TRI gave none), the primary NAICS code of that submission (`naics_code`, 2 to 6 digits, null if TRI gave none or an implausible value), that code's title in words (`naics_title`, from the local Census code lists; null when the code is missing or not listed), `total_release` as a finite non-negative number, the unit exactly as reported by TRI, the emission rate in g/s, the operating hours per year used to compute it, the source of those hours (`operating_hours_source`), latitude and longitude in decimal degrees, and street address, city, county, state and ZIP code. `total_release` and its unit SHALL be the reported values, unconverted.

#### Scenario: Complete record
- **WHEN** a facility record is returned
- **THEN** it includes every field above, with `total_release` in the returned unit, `emission_rate` in g/s, and a non-empty `operating_hours_source`

#### Scenario: Title from the local lists
- **WHEN** the record's NAICS code is a six-digit code in the local code lists
- **THEN** `naics_title` is that code's title, with no request made

#### Scenario: Unlisted or missing code
- **WHEN** the record has no NAICS code, or one the local lists lack
- **THEN** `naics_title` is null

#### Scenario: Control number carried
- **WHEN** the TRI row has a control number
- **THEN** the record carries it as text of digits, ready for the facility industry tool

#### Scenario: Reported value preserved
- **WHEN** TRI reports the quantity in "Pounds"
- **THEN** the record carries the same number and the unit "Pounds" in `total_release` and `unit`, alongside the converted `emission_rate`

### Requirement: Emission rate from annual release
The system SHALL convert each annual release to an emission rate in g/s by converting the quantity to grams with the shared unit conversion and dividing by the operating seconds per year. The operating hours per year SHALL be those of the facility's industry from the Census plant-hours baseline, matched on the facility's NAICS code (most specific prefix first), and otherwise the configured default (default 8,760, continuous operation); the choice SHALL be made through a single dedicated function, and the hours and their source SHALL be reported on each record. A row whose unit cannot be converted to grams SHALL be discarded with a counted warning, never passed through unconverted.

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
