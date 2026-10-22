## MODIFIED Requirements

### Requirement: Returned facility record
Each returned record SHALL contain the facility FRS ID, facility name, environmental medium, reporting year, the TRI submission control number (`doc_ctrl_num`, null if TRI gave none), the primary NAICS code of that submission (`naics_code`, 2 to 6 digits, null if TRI gave none or an implausible value), that code's title in words (`naics_title`, from the local Census code lists; null when the code is missing or not listed), `total_release` as a finite non-negative number, the unit exactly as reported by TRI, the emission rate in g/s, the operating hours per year used to compute it, the source of those hours (`operating_hours_source`), the TSCA conditions of use of the facility's reported activities (`conditions_of_use`), their distinct life cycle stages (`lifecycle_stages`) and a note saying why they are empty when they are (`conditions_note`), latitude and longitude in decimal degrees, and street address, city, county, state and ZIP code. `total_release` and its unit SHALL be the reported values, unconverted.

#### Scenario: Complete record
- **WHEN** a facility record is returned
- **THEN** it includes every field above, with `total_release` in the returned unit, `emission_rate` in g/s, a non-empty `operating_hours_source`, and `conditions_of_use`, `lifecycle_stages` and `conditions_note` as lists and text per the conditions-of-use capability

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

#### Scenario: Conditions carried
- **WHEN** the facility's latest submission reports Section 3.2a
- **THEN** the record's `conditions_of_use` has the Processing, "Processing as a reactant" condition and `lifecycle_stages` is ["Processing"]
