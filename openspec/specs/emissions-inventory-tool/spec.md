# emissions-inventory-tool Specification

## Purpose

Lets the agent discover which facilities report releasing a chemical to selected environmental media, where they are, and how much they released in their most recent reporting year, using EPA TRI data.

## Requirements

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

### Requirement: Medium filter from configuration
The system SHALL keep only rows whose environmental medium is in the configured list (initially `AIR STACK`); rows for other media SHALL be discarded.

#### Scenario: Only stack air
- **WHEN** TRI rows include AIR STACK, LAND TREA and OTH DISP for a facility
- **THEN** only the AIR STACK record is returned

#### Scenario: Adding a medium
- **WHEN** another medium name is added to the configured list
- **THEN** its records are returned with no code change

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

### Requirement: Inventory reused for a configured time
The inventory of a chemical for a place SHALL be reused, for the configured time, by later inventory calls and by the batch assessment within the same process, so TRI is read once; copies SHALL be returned, so a caller cannot change the remembered inventory.

#### Scenario: Listing then assessing
- **WHEN** the inventory is listed and the same chemical is then assessed within the reuse time
- **THEN** TRI is read once

#### Scenario: Reuse off
- **WHEN** the reuse time is 0
- **THEN** every call reads TRI

### Requirement: EIS IDs of many facilities, quickly
The same-site searches of facilities without their own EIS registration SHALL run a configured number at a time, the EIS registrations of all the twins found SHALL be read together, and each facility's EIS IDs (or the reason it has none) SHALL be reused for a configured time within the process, so assessing hundreds of facilities stays practical and a repeated assessment makes no new EIS request.

#### Scenario: Repeated lookup
- **WHEN** the EIS IDs of the same facilities are asked for again within the reuse time
- **THEN** no request is made

#### Scenario: Twin registrations together
- **WHEN** several facilities need a same-site search
- **THEN** the registrations of every twin found are read in bulk, not one request per facility

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
