## MODIFIED Requirements

### Requirement: Latest year per facility and medium
The system SHALL keep, for each combination of environmental medium and facility FRS ID, only the record with the latest reporting year, considering only reports of the last `recent_years` TRI reporting years; the window SHALL be applied in the TRI request itself (reporting year after the current year minus `recent_years`) and rows outside it SHALL be ignored with a warning count. The facility FRS ID SHALL be the EPA registry identifier TRI records for the facility, falling back to TRI's separate FRS ID column when the registry identifier is absent; a row with neither is skipped with a warning.

#### Scenario: Several years reported
- **WHEN** a facility reported to AIR STACK in each of the last three years of the window
- **THEN** only the newest of them is returned for that facility and medium

#### Scenario: Reported only before the window
- **WHEN** a facility's latest report is older than the window
- **THEN** the facility is absent from the result

#### Scenario: Window in the request
- **WHEN** the current year is 2012 and `recent_years` is 10
- **THEN** the TRI request filters reporting years after 2002

#### Scenario: Latest year not reported
- **WHEN** the latest-year record has no release quantity (not applicable or empty)
- **THEN** the facility is omitted for that medium rather than falling back to an older year, and the omission is counted in a warning

#### Scenario: Different media
- **WHEN** one facility reported to two configured media
- **THEN** it appears once per medium, each with its own latest year

#### Scenario: Several reports in the latest year
- **WHEN** a facility has two reports for the same medium in its latest year
- **THEN** their valid quantities are added and returned as one record, carrying the highest control number of the reports that gave a quantity

### Requirement: Returned facility record
Each returned record SHALL contain the facility FRS ID, facility name, environmental medium, reporting year, the TRI submission control number (`doc_ctrl_num`, null if TRI gave none), `total_release` as a finite non-negative number, the unit exactly as reported by TRI, the emission rate in g/s, the operating hours per year used to compute it, latitude and longitude in decimal degrees, and street address, city, county, state and ZIP code. `total_release` and its unit SHALL be the reported values, unconverted.

#### Scenario: Complete record
- **WHEN** a facility record is returned
- **THEN** it includes every field above, with `total_release` in the returned unit and `emission_rate` in g/s

#### Scenario: Control number carried
- **WHEN** the TRI row has a control number
- **THEN** the record carries it as text of digits, ready for the facility industry tool

#### Scenario: Reported value preserved
- **WHEN** TRI reports the quantity in "Pounds"
- **THEN** the record carries the same number and the unit "Pounds" in `total_release` and `unit`, alongside the converted `emission_rate`

## ADDED Requirements

### Requirement: Coordinates recovered from FRS
When none of a facility's TRI rows in the window has valid coordinates, and the facility has a usable release quantity, the system SHALL look the facility up by FRS ID in the Envirofacts FRS point table (`[frs_point]`) and use the newest valid point (decimal degrees, west negative, within range). It SHALL NOT make that request for a facility that has TRI coordinates or no usable quantity, SHALL make at most one request per FRS ID, and SHALL count recovered facilities in a warning. A failed request or an unusable point SHALL leave the facility omitted and counted as without coordinates; it SHALL NOT raise.

#### Scenario: TRI has no coordinates, FRS has
- **WHEN** a facility's TRI rows lack coordinates and FRS returns a valid point
- **THEN** the record carries the FRS latitude and longitude and a warning counts the facility as located from FRS

#### Scenario: TRI coordinates win
- **WHEN** a TRI row has valid coordinates
- **THEN** FRS is not queried

#### Scenario: FRS has nothing
- **WHEN** FRS returns no valid point or the request fails
- **THEN** the facility is omitted and counted as without coordinates
