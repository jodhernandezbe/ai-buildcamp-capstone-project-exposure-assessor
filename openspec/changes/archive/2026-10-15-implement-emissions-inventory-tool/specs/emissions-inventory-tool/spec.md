## Purpose

Lets the agent discover which facilities report releasing a chemical to selected environmental media, where they are, and how much they released in their most recent reporting year, using EPA TRI data.

## ADDED Requirements

### Requirement: Facility emissions lookup by CAS
The system SHALL provide a tool that, given a CAS registry number, returns the facilities that reported releases of that chemical to the configured environmental media. The tool SHALL NOT take a reporting year. The CAS number SHALL be validated before any request is made; an invalid CAS yields an empty result with a warning and no request.

#### Scenario: Known chemical
- **WHEN** the tool is called with a CAS number that TRI facilities have reported
- **THEN** it returns one record per (environmental medium, facility) for the configured media

#### Scenario: Invalid CAS
- **WHEN** the tool is called with a string that is not a valid CAS number
- **THEN** it returns an empty list, logs a warning, and makes no HTTP request

#### Scenario: Chemical never reported
- **WHEN** TRI has no rows for the CAS number
- **THEN** it returns an empty list

### Requirement: Latest year per facility and medium
The system SHALL keep, for each combination of environmental medium and facility FRS ID, only the record with the latest reporting year. The facility FRS ID SHALL be the EPA registry identifier TRI records for the facility, falling back to TRI's separate FRS ID column when the registry identifier is absent; a row with neither is skipped with a warning.

#### Scenario: Several years reported
- **WHEN** a facility reported to AIR STACK in 1990, 2005 and 2022
- **THEN** only the 2022 record is returned for that facility and medium

#### Scenario: Latest year not reported
- **WHEN** the latest-year record has no release quantity (not applicable or empty)
- **THEN** the facility is omitted for that medium rather than falling back to an older year, and the omission is counted in a warning

#### Scenario: Different media
- **WHEN** one facility reported to two configured media
- **THEN** it appears once per medium, each with its own latest year

#### Scenario: Several reports in the latest year
- **WHEN** a facility has two reports for the same medium in its latest year (for example 909 and 2683 pounds)
- **THEN** their valid quantities are added (3592 pounds) and returned as one record, and a warning counts the combined facilities

### Requirement: Medium filter from configuration
The system SHALL keep only rows whose environmental medium is in the configured list (initially `AIR STACK`); rows for other media SHALL be discarded.

#### Scenario: Only stack air
- **WHEN** TRI rows include AIR STACK, LAND TREA and OTH DISP for a facility
- **THEN** only the AIR STACK record is returned

#### Scenario: Adding a medium
- **WHEN** another medium name is added to the configured list
- **THEN** its records are returned with no code change

### Requirement: Returned facility record
Each returned record SHALL contain the facility FRS ID, facility name, environmental medium, reporting year, `total_release` as a finite non-negative number, the unit exactly as reported by TRI, the emission rate in g/s, the operating hours per year used to compute it, latitude and longitude in decimal degrees, and street address, city, county, state and ZIP code. `total_release` and its unit SHALL be the reported values, unconverted.

#### Scenario: Complete record
- **WHEN** a facility record is returned
- **THEN** it includes every field above, with `total_release` in the returned unit and `emission_rate` in g/s

#### Scenario: Reported value preserved
- **WHEN** TRI reports the quantity in "Pounds"
- **THEN** the record carries the same number and the unit "Pounds" in `total_release` and `unit`, alongside the converted `emission_rate`

### Requirement: Emission rate from annual release
The system SHALL convert each annual release to an emission rate in g/s by converting the quantity to grams with the shared unit conversion and dividing by the operating seconds per year. The operating hours per year SHALL come from the configuration (default 8,760, continuous operation) through a single dedicated function, and SHALL be reported on each record. A row whose unit cannot be converted to grams SHALL be discarded with a counted warning, never passed through unconverted.

#### Scenario: Pounds per year to g/s
- **WHEN** a facility reports 8,760 pounds in a year and the operating hours are 8,760
- **THEN** the emission rate is 8,760 pounds in grams divided by 31,536,000 s (about 0.126 g/s)

#### Scenario: Configured hours
- **WHEN** the configured operating hours per year are changed
- **THEN** the emission rate and the reported hours change with no code change

#### Scenario: Unconvertible unit
- **WHEN** a row's unit is unknown or not a mass
- **THEN** the row is not returned and a warning counts it

#### Scenario: Invalid hours
- **WHEN** the configured operating hours are zero, negative, above the number of hours in a year, or non-numeric
- **THEN** the settings loader raises a `ValueError` and no lookup is made

### Requirement: Fail-closed data validation
The system SHALL treat TRI data as untrusted. A row SHALL be discarded with a counted warning when its release quantity is missing, non-numeric, boolean, non-finite or negative, or when its unit is missing. A facility's coordinates SHALL be taken from its most recent row that has valid ones (finite, within latitude/longitude ranges), because the latest row often lacks them; a facility with no valid coordinates in any retrieved row SHALL be omitted with a counted warning. Longitude SHALL be reported as signed decimal degrees (negative west of Greenwich) and SHALL NOT be guessed when the hemisphere cannot be determined.

#### Scenario: Bad quantity
- **WHEN** a row has a null, negative, NaN or boolean `total_release`
- **THEN** the row is not returned and a warning counts it

#### Scenario: Coordinates only on an older row
- **WHEN** a facility's latest-year row has no coordinates but an earlier row does
- **THEN** the record uses the latest year's quantity with the earlier row's coordinates

#### Scenario: No coordinates anywhere
- **WHEN** no retrieved row of a facility has usable coordinates
- **THEN** the facility is not returned and a warning counts it

#### Scenario: Western longitude
- **WHEN** TRI gives a longitude as an unsigned magnitude for a facility in a western-hemisphere state
- **THEN** the returned longitude is negative

### Requirement: Paged, throttled retrieval
The system SHALL retrieve rows sequentially in pages of a configured size, wait the configured delay between requests, bound every request by the configured timeout, and stop when a page is shorter than the page size or empty, or when the configured page cap is reached. It SHALL retry throttling (HTTP 429) and transient server errors a configured number of times with increasing waits, honouring a `Retry-After` header when present. Rows SHALL be reduced to the kept records page by page.

#### Scenario: Multiple pages
- **WHEN** the first page is full and the second is shorter
- **THEN** exactly two requests are made, the second starting after the first page's rows

#### Scenario: Throttled
- **WHEN** a request returns HTTP 429 and a later attempt succeeds
- **THEN** the tool waits and retries, and returns the data

#### Scenario: Retries exhausted
- **WHEN** a page keeps failing after the configured retries
- **THEN** the tool returns no partial result as if complete: it reports the failure with a warning and an empty list

#### Scenario: Page cap
- **WHEN** the page cap is reached before a short page
- **THEN** retrieval stops and the result is flagged as possibly incomplete in a warning

#### Scenario: Unexpected response shape
- **WHEN** a response is not a JSON list of objects
- **THEN** it is treated as a failed page, not as data
