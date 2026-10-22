## ADDED Requirements

### Requirement: Longest-prefix match of a NAICS code
The system SHALL resolve a facility's operating hours from the QPC baseline by trying its NAICS code and then each shorter prefix, from the code's own length down to the configured minimum (three digits), and SHALL use the first prefix that has a baseline row, so the most specific match wins. A prefix SHALL only be tried when it is a prefix of the facility's code: a facility with a four-digit code SHALL NOT match a longer baseline code beneath it. The code SHALL be a string of ASCII digits of two to six digits; anything else has no match.

#### Scenario: Exact six-digit match
- **WHEN** the facility's code is 325211 and the baseline has rows for 325211 and 3252
- **THEN** the 325211 row is used

#### Scenario: Falls back to a shorter code
- **WHEN** the facility's code is 325211 and the baseline has rows for 3252 and 325 but not 325211 or 32521
- **THEN** the 3252 row is used

#### Scenario: Specific beats general
- **WHEN** the baseline has rows for 325, 3252 and 32521 and the facility's code is 325211
- **THEN** the 32521 row is used

#### Scenario: Never matches a more specific baseline code
- **WHEN** the facility's code is 3252 and the baseline has only a row for 325211
- **THEN** there is no match

#### Scenario: No row for any prefix
- **WHEN** no prefix of the facility's code, down to three digits, has a row
- **THEN** there is no match

#### Scenario: Unusable codes
- **WHEN** the code is missing, empty, has non-digit characters, has one digit, or has more than six digits
- **THEN** there is no match and no error is raised

### Requirement: Efficient matching
The system SHALL read and validate the baseline file once per process into an immutable mapping from code to hours, and SHALL resolve each facility with at most one dictionary probe per candidate prefix (at most four for a six-digit code), without scanning the table, reading the file again, or using a dataframe at lookup time.

#### Scenario: One read
- **WHEN** many facilities are resolved in one run
- **THEN** the baseline file is read once

#### Scenario: Bounded probes
- **WHEN** a six-digit code is resolved
- **THEN** at most four prefixes (six, five, four and three digits) are probed

### Requirement: Hours per week become hours per year
The system SHALL convert the matched average plant hours per week to operating hours per year as hours per week multiplied by the configured days per year (365) divided by seven, so that 168 hours per week gives exactly 8,760 hours per year. The result SHALL be positive and at most 8,760.

#### Scenario: Continuous operation
- **WHEN** the matched value is 168 hours per week
- **THEN** the operating hours per year are 8,760

#### Scenario: Part-time operation
- **WHEN** the matched value is 84 hours per week
- **THEN** the operating hours per year are 4,380

### Requirement: Fallback to the configured default
The system SHALL use the configured default operating hours per year (`[emissions]`, 8,760) when there is no match, and SHALL do so without error. When the baseline file is missing, unreadable or invalid as a whole, the system SHALL use the default for every facility and say so once in the inventory's warnings, rather than fail the lookup.

#### Scenario: No match
- **WHEN** a facility has no baseline match
- **THEN** its hours are the configured default and its source says so

#### Scenario: Baseline file missing
- **WHEN** the baseline file does not exist
- **THEN** every facility uses the default and one warning names the file

### Requirement: Baseline is validated and fails closed
The system SHALL treat the baseline file as untrusted input. A row SHALL be ignored, with one counted warning, when its code is not an ASCII digit string of three to six digits, when its hours are not a finite number that is not a boolean and in (0, 168], or when its code appears more than once. The file SHALL be rejected as a whole when a configured column is missing or its release metadata is absent.

#### Scenario: Bad row
- **WHEN** a row has hours of 0, 169, NaN, a boolean or null
- **THEN** that row is ignored, a warning counts it, and other rows still match

#### Scenario: Duplicate code
- **WHEN** a code appears twice in the file
- **THEN** neither row is used for that code

#### Scenario: Missing column
- **WHEN** the configured hours column is not in the file
- **THEN** the file is rejected and the default is used with a warning

### Requirement: Source of the hours is stated
The system SHALL produce, for each resolution, a short source string: for a match, the QPC release, the matched baseline code and its hours per week; for a fallback, that the configured default was used and why (no code, no match, or baseline unavailable).

#### Scenario: Matched
- **WHEN** code 325211 matches the 3252 row of release 2026Q2 with 111.7 hours per week
- **THEN** the source names Census QPC 2026Q2, code 3252 and 111.7 hours per week

#### Scenario: Default
- **WHEN** there is no match
- **THEN** the source says the configured default of 8,760 hours per year was used, and why

### Requirement: Configuration, not code
The system SHALL read the baseline path, the code and hours column names, the minimum and maximum prefix length, the days per year and the maximum hours per week from a typed `[plant_hours]` section of `config/settings.toml`, validated on load with errors naming the key, and SHALL NOT embed them in Python code.

#### Scenario: Renamed column
- **WHEN** the hours column name in configuration is changed
- **THEN** the new column is read with no code change

#### Scenario: Invalid setting
- **WHEN** the minimum prefix length is below 1, above the maximum, or the days per year is not a positive finite number
- **THEN** loading fails with an error naming the key
