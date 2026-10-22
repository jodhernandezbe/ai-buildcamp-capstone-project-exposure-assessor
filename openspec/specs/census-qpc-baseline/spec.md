# census-qpc-baseline Specification

## Purpose
Builds a versioned, validated baseline of average plant hours per week by four-digit NAICS code from the Census Bureau's Quarterly Survey of Plant Capacity Utilization, never guessing a value it cannot attribute.

## Requirements

### Requirement: Release two quarters behind
The system SHALL choose the QPC release to download from the current date: the calendar quarter that is the configured number of quarters (two) before the current one, crossing year boundaries. The year and quarter SHALL be substituted into the configured URL template.

#### Scenario: Same year
- **WHEN** the current date is in 2026 Q4
- **THEN** the release is 2026 Q2

#### Scenario: Previous year
- **WHEN** the current date is in 2026 Q2
- **THEN** the release is 2025 Q4

#### Scenario: Quarter 1
- **WHEN** the current date is in 2026 Q1
- **THEN** the release is 2025 Q3

#### Scenario: Release not published
- **WHEN** the server answers 404 for the chosen release
- **THEN** the script exits with an error naming the release and URL, and does not fall back to another release or touch the existing parquet

### Requirement: Safe download
The system SHALL fetch the workbook over HTTPS from the configured host with a timeout and a size cap, and SHALL accept it only when it is a ZIP-based workbook. A failed, truncated or oversized download SHALL be an error that leaves any existing parquet unchanged.

#### Scenario: Non-HTTPS or foreign host
- **WHEN** the configured URL template is not an https URL on the configured host
- **THEN** the configuration fails to load, naming the key

#### Scenario: Not a workbook
- **WHEN** the response body is not a ZIP archive (e.g. an HTML error page with status 200)
- **THEN** the script exits with an error and writes nothing

#### Scenario: Oversized response
- **WHEN** the body exceeds the configured size cap
- **THEN** the download is abandoned with an error and nothing is written

### Requirement: Workbook is the release that was asked for
The system SHALL verify, before reading any value, that the configured sheet exists, that the sheet title names the requested year and quarter, that the requested quarter's block is the one read, and that the workbook states the configured NAICS edition. The header row and the hours column SHALL be found by their configured labels (whitespace-normalised), not by fixed positions.

#### Scenario: Matching release
- **WHEN** the sheet title says "2026 Quarter 2" and the first block is headed "Quarter 2"
- **THEN** the hours column of that block is read

#### Scenario: Wrong quarter inside the file
- **WHEN** the sheet title names a different year or quarter than requested
- **THEN** the script exits with an error naming both and writes nothing

#### Scenario: Sheet or column missing
- **WHEN** the configured sheet or the "Average plant hours per week in operation" header is absent
- **THEN** the script exits with an error naming what was not found and the labels that were

#### Scenario: Different NAICS edition
- **WHEN** the workbook states a NAICS edition other than the configured one
- **THEN** the script exits with an error, because 4-digit codes would not be comparable

#### Scenario: Previous quarter's block is not used
- **WHEN** the sheet also carries the previous quarter's hours to the right
- **THEN** none of those values reach the output

### Requirement: Published code expressions expand to 4-digit codes
The system SHALL parse each published code cell into the NAICS codes it covers, after removing footnote markers such as ` 1/`. Comma lists replace trailing digits of the first code (`3111,7,8` is 3111, 3117, 3118), hyphen ranges span the last digit (`3321,2,4-6` is 3321, 3322, 3324, 3325, 3326; `332992-4` is 332992, 332993, 332994), and cells that are numbers are treated as their digits. A 4-digit code SHALL be output only when one source row covers it entirely: a 4-digit expression yields its codes, and a 3-digit code yields the 4-digit codes beneath it in the local NAICS titles table for the configured edition. The same value applies to every 4-digit code the row covers.

#### Scenario: Group of 4-digit codes
- **WHEN** the row `3111,7,8` has 99.0 hours
- **THEN** 3111, 3117 and 3118 each get 99.0 hours and the same source code text

#### Scenario: Range in a group
- **WHEN** the row is `3321,2,4-6`
- **THEN** 3321, 3322, 3324, 3325 and 3326 each get its value and 3323 is not covered by it

#### Scenario: Three-digit row
- **WHEN** the row is `313` and the titles table lists 3131, 3132 and 3133 for the configured edition
- **THEN** those three codes get the row's value

#### Scenario: Numeric cell
- **WHEN** a code cell is the integer 3112 rather than text
- **THEN** it is read as 3112

#### Scenario: Footnote marker
- **WHEN** the cell reads `51312 3/`
- **THEN** the footnote marker is removed before parsing

### Requirement: Never guess a 4-digit value
The system SHALL leave out, and report with a reason, every row that cannot be attributed to whole 4-digit codes: rows covering part of a 4-digit code (5- or 6-digit expressions), aggregate rows shorter than three digits (e.g. `31-33`), rows whose hours are withheld (`D`) or not a finite number, rows whose hours are outside the configured plausible range, and rows that cover a 4-digit code already covered by another row. No value SHALL be averaged, apportioned or carried across rows.

#### Scenario: Sub-four-digit row
- **WHEN** the row is `32411` (Petroleum refineries) and another row `32412,9` is under the same 4-digit code 3241
- **THEN** 3241 is absent from the output and both rows are reported as covering only part of a 4-digit code

#### Scenario: Withheld
- **WHEN** the hours cell is `D`
- **THEN** the row's codes are absent and the report says the estimate was withheld

#### Scenario: Implausible hours
- **WHEN** the hours are negative, zero, above 168 (hours in a week), NaN, or a boolean
- **THEN** the row's codes are absent and the report says why

#### Scenario: Continuous operation
- **WHEN** the hours are exactly 168 (24 h x 7 d)
- **THEN** the value is kept

#### Scenario: Overlapping rows
- **WHEN** two rows cover the same 4-digit code
- **THEN** that code is absent and both rows are reported

#### Scenario: Unparseable code cell
- **WHEN** a cell in the code column looks like data (has a value in the hours column) but parses to no code
- **THEN** it is reported as skipped, not silently dropped

### Requirement: Structural sanity before writing
The system SHALL refuse to write the parquet when the result looks like a layout change: fewer 4-digit codes than the configured minimum, no data row found after the header, or a code-column cell that parses but whose description is empty.

#### Scenario: Too few codes
- **WHEN** fewer than the configured minimum of 4-digit codes survive
- **THEN** the script exits with an error and the existing parquet is unchanged

#### Scenario: Valid workbook
- **WHEN** all checks pass
- **THEN** the parquet is written and a summary of codes written and rows skipped, with reasons, is printed

### Requirement: Versioned parquet by 4-digit NAICS code
The system SHALL write `data/census_qpc_baseline.parquet` (path from configuration) with one row per 4-digit NAICS code, sorted by code, with columns: `naics_code` (string, four digits), `avg_plant_hours_per_week` (float64, hours per week), `source_naics` (the published code text, footnote removed), `source_title` (the published description), `release_year` (int) and `release_quarter` (int, 1-4). The file's metadata SHALL state the release, the source URL, the SHA-256 of the downloaded workbook, the retrieval date, and the NAICS edition. The write SHALL be atomic and the output deterministic for a given workbook apart from the retrieval date.

#### Scenario: One row per code
- **WHEN** the file is read back
- **THEN** `naics_code` is unique, four digits, and sorted

#### Scenario: Release recorded
- **WHEN** the file is read back
- **THEN** every row has the release year and quarter and the file metadata has the URL and workbook SHA-256

#### Scenario: Failed run keeps previous file
- **WHEN** any check fails or the process is interrupted during writing
- **THEN** the previous parquet is byte-for-byte unchanged and no partial file remains

#### Scenario: Re-run on the same release
- **WHEN** the script is run twice against the same workbook
- **THEN** the rows are identical

### Requirement: Configuration, not code
The system SHALL read the URL template, host, lag in quarters, sheet name, code and hours header labels, title-cell pattern, NAICS edition, hours bounds, minimum code count, timeout, size cap and output path from a typed `[qpc]` section of `config/settings.toml`. A malformed value SHALL fail at load time naming the key.

#### Scenario: Sheet renamed upstream
- **WHEN** the sheet name in configuration is changed
- **THEN** the script reads the new sheet with no code change

#### Scenario: Invalid setting
- **WHEN** `lag_quarters` is negative, `max_hours_per_week` is not a positive finite number, or the URL template lacks `{year}` or `{quarter}`
- **THEN** loading fails with an error naming the key

### Requirement: Testable without the network
The script SHALL take the current date and the downloader as injectable collaborators, so its behaviour is tested with in-memory workbooks and fixed dates, without network access.

#### Scenario: Injected date
- **WHEN** tests supply the date 2026-10-22
- **THEN** the chosen release is 2026 Q2
