## MODIFIED Requirements

### Requirement: Returned facility record
Each returned record SHALL contain the facility FRS ID, facility name, environmental medium, reporting year, the TRI submission control number (`doc_ctrl_num`, null if TRI gave none), the primary NAICS code of that submission (`naics_code`, 2 to 6 digits, null if TRI gave none or an implausible value), that code's title in words (`naics_title`, from the local Census code lists; null when the code is missing or not listed), `total_release` as a finite non-negative number, the unit exactly as reported by TRI, the emission rate in g/s, the operating hours per year used to compute it, latitude and longitude in decimal degrees, and street address, city, county, state and ZIP code. `total_release` and its unit SHALL be the reported values, unconverted.

#### Scenario: Complete record
- **WHEN** a facility record is returned
- **THEN** it includes every field above, with `total_release` in the returned unit and `emission_rate` in g/s

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

### Requirement: Primary NAICS code from the submission
The TRI request SHALL join the submission-NAICS table so every row carries a NAICS code and its primary indicator. A submission with secondary NAICS codes is returned once per code; the system SHALL keep only its primary row (indicator `1`), counting the others in a warning, so that no release is added more than once. A row without the indicator (no NAICS joined) SHALL be kept with no code. The record's NAICS code SHALL be that of the submission whose control number the record carries (the highest of the latest year's reports), or, when that submission has none, of another report of the same year. The reducer returns the code only; the tool adds the title from the local Census code lists before ranking.

#### Scenario: Secondary codes
- **WHEN** a submission comes back three times, for its primary and two secondary NAICS codes
- **THEN** its release is counted once, the record carries the primary code and a warning counts two ignored rows

#### Scenario: No NAICS joined
- **WHEN** a row has no primary indicator
- **THEN** it is kept and the record's `naics_code` is null

#### Scenario: Same totals as without the join
- **WHEN** the inventory of a chemical is read with and without the NAICS join
- **THEN** the same facilities are returned with the same releases

## ADDED Requirements

### Requirement: EIS IDs of the listed facilities
The tool SHALL look up the NEI (EIS) facility IDs registered in FRS for the facilities it lists, many per request, and carry them in each listed record as `eis_ids` (empty when none). For a listed facility whose own FRS ID has no EIS registration, the tool SHALL look for other FRS records of exactly the same site name in the same state within a configured distance and use the EIS IDs of such a record only when exactly one of them has EIS registrations; `eis_note` SHALL say that the IDs are borrowed and from which FRS ID, or why none could be found. A failed lookup SHALL leave the facilities without IDs and a note, never raise. Facilities beyond the listed ones SHALL NOT be looked up.

#### Scenario: Registered facility
- **WHEN** FRS registers EIS facilities for a listed facility's FRS ID
- **THEN** the record carries those distinct EIS IDs and no note

#### Scenario: Same site under another FRS ID
- **WHEN** the facility's FRS ID has no EIS registration and exactly one other FRS record of the same name and state within the distance has one
- **THEN** the record carries that record's EIS IDs and the note names it and the distance

#### Scenario: Ambiguous or absent twins
- **WHEN** no same-named record is within reach, none of them has an EIS registration, or more than one has
- **THEN** `eis_ids` is empty and the note says which

#### Scenario: Lookup failure
- **WHEN** the FRS service cannot be reached
- **THEN** every listed record has empty `eis_ids` and a note, and the inventory is still returned

### Requirement: Tool description says the listing is not the set to assess
The tool's description SHALL say that the listing holds the largest sources and how many were left out, that the listing is not the set to assess because a small emitter can matter as much as a large one and every facility found stays available to the assessment, that the record carries the industry's title and nothing about its process, and that zero facilities is not evidence that nobody emits the chemical.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it says every facility found stays available to the assessment and no longer tells the model to decide which facilities to assess
