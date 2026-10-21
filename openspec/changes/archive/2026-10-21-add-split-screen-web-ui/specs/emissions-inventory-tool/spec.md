## MODIFIED Requirements

### Requirement: Facility emissions lookup by CAS
The system SHALL provide a tool that, given a CAS registry number, returns the facilities that reported releases of that chemical to the configured environmental media. The tool SHALL NOT take a reporting year. The CAS number SHALL be validated before any request is made; an invalid CAS yields an empty result with a warning and no request.

The tool SHALL tell the model only the largest facilities. It SHALL return to the model the number of facilities found (`total_found`), the number matching the filters (`matching`), the number listed (`shown`), a `note` that says the list is partial when it is (null otherwise), and at most `[tri] max_listed` facilities ordered by emission rate, highest first. It SHALL also return the complete matching list, in the same order, as a tool artifact that the model never sees, for the program (the workspace). It MAY be given an optional `state` (postal abbreviation) and an optional `city` (exact name), both case-insensitive, which restrict `matching`, the listed facilities and the artifact to that place while `total_found` stays unfiltered.

#### Scenario: Known chemical
- **WHEN** the tool is called with a CAS number that TRI facilities have reported
- **THEN** the complete list has one record per (environmental medium, facility) for the configured media, and the model is told the largest of them

#### Scenario: Invalid CAS
- **WHEN** the tool is called with a string that is not a valid CAS number
- **THEN** it returns no facilities, logs a warning, and makes no HTTP request

#### Scenario: Chemical never reported
- **WHEN** TRI has no rows for the CAS number
- **THEN** it returns no facilities

#### Scenario: Many facilities
- **WHEN** more facilities match than `[tri] max_listed`
- **THEN** the model is told the `max_listed` with the highest emission rates, highest first, and a note that the list is partial, while the artifact holds every matching facility

#### Scenario: Place filter
- **WHEN** the tool is called with `state` "tx" or with `city` "houston"
- **THEN** only facilities there are matched, listed and in the artifact, and `total_found` still counts every facility found

#### Scenario: Nothing matches the filter
- **WHEN** no facility matches the given `state` and `city`
- **THEN** `matching` and `shown` are 0 and the note says that no facility matches

### Requirement: Latest year per facility and medium
The system SHALL keep, for each combination of environmental medium and facility FRS ID, only the record with the latest reporting year, considering only the last `recent_years` TRI reporting years ending with the newest year that can have been published, that is the current year minus `publication_lag_years` (TRI for year N is released annually by June of N + 1); the window SHALL be applied in the TRI request itself (reporting year after the current year minus `publication_lag_years` minus `recent_years`) and rows outside it SHALL be ignored with a warning count. The shipped window is the last 2 published years. The facility FRS ID SHALL be the EPA registry identifier TRI records for the facility, falling back to TRI's separate FRS ID column when the registry identifier is absent; a row with neither is skipped with a warning.

#### Scenario: Several years reported
- **WHEN** a facility reported to AIR STACK in each of the last three years of the window
- **THEN** only the newest of them is returned for that facility and medium

#### Scenario: Reported only before the window
- **WHEN** a facility's latest report is older than the window
- **THEN** the facility is absent from the result

#### Scenario: Window in the request
- **WHEN** the current year is 2026, `recent_years` is 2 and `publication_lag_years` is 1
- **THEN** the TRI request filters reporting years after 2023, so 2024 and 2025 count

#### Scenario: Latest year not reported
- **WHEN** the latest-year record has no release quantity (not applicable or empty)
- **THEN** the facility is omitted for that medium rather than falling back to an older year, and the omission is counted in a warning

#### Scenario: Different media
- **WHEN** one facility reported to two configured media
- **THEN** it appears once per medium, each with its own latest year

#### Scenario: Several reports in the latest year
- **WHEN** a facility has two reports for the same medium in its latest year
- **THEN** their valid quantities are added and returned as one record, carrying the highest control number of the reports that gave a quantity

### Requirement: Coordinates recovered from FRS
When none of a facility's TRI rows in the window has valid coordinates, and the facility has a usable release quantity, the system SHALL look the facility up by FRS ID in the EPA FRS best-pick lookup (`[frs_point]`, a separate service from Envirofacts) and use its point (decimal degrees, west negative, within range). Facilities SHALL be looked up in bulk: all such facilities of one inventory are asked together, at most `[frs_point] batch_size` FRS IDs per request, never one request per facility. It SHALL NOT ask for a facility that has TRI coordinates or no usable quantity, SHALL ask for each FRS ID at most once, SHALL keep only rows for IDs it asked for, and SHALL count recovered facilities in a warning. A failed request or an unusable point SHALL leave the affected facilities omitted and counted as without coordinates, and SHALL NOT raise or lose the other batches.

#### Scenario: TRI has no coordinates, FRS has
- **WHEN** a facility's TRI rows lack coordinates and FRS returns a valid point
- **THEN** the record carries the FRS latitude and longitude and a warning counts the facility as located from FRS

#### Scenario: TRI coordinates win
- **WHEN** a TRI row has valid coordinates
- **THEN** FRS is not queried

#### Scenario: FRS has nothing
- **WHEN** FRS returns no valid point or the request fails
- **THEN** the facility is omitted and counted as without coordinates

#### Scenario: Many facilities, few requests
- **WHEN** 250 facilities lack TRI coordinates and `batch_size` is 100
- **THEN** FRS is asked 3 times, not 250

#### Scenario: One batch fails
- **WHEN** one of several batches fails
- **THEN** only its facilities are left without coordinates
