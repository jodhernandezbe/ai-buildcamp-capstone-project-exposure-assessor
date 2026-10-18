## ADDED Requirements

### Requirement: Industry settings
The system SHALL read from an `[industry]` table the Envirofacts path that lists the primary NAICS row of a submission (containing `{doc_ctrl_num}`) and the one that looks up a NAICS title (containing `{naics_code}`), the response field names (code, primary indicator, sequence, origin, title), the primary-indicator value, the origin labels for reported and assigned codes, and the placeholder codes, validated on load, and SHALL NOT embed them in Python code. The base URL and request policy SHALL be the shared Envirofacts ones.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the industry settings
- **THEN** it returns the paths, field names, labels and placeholder codes from the file

#### Scenario: Invalid entry
- **WHEN** a path lacks its placeholder, a field name or label is empty, or a placeholder is not a digit string
- **THEN** the loader raises a `ValueError` naming the offending key

### Requirement: Recent TRI years setting
The `[tri]` table SHALL define `recent_years`, a positive integer, and a `{after_year}` placeholder in the release path, and the loader SHALL reject a missing, non-integer, boolean or non-positive value and a path without the placeholder.

#### Scenario: Window years
- **WHEN** `recent_years` is 10 and the current year is 2026
- **THEN** the settings give 2016 as the year after which reports count and 2017 as the first year

#### Scenario: Invalid window
- **WHEN** `recent_years` is 0, true or 2.5
- **THEN** the loader raises a `ValueError` naming `recent_years`

### Requirement: FRS point settings
The system SHALL read from an `[frs_point]` table the Envirofacts path that returns a facility's coordinates (containing `{frs_id}`) and the latitude, longitude and timestamp field names, validated on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the FRS point settings
- **THEN** it returns the path and field names from the file

#### Scenario: Invalid entry
- **WHEN** the path lacks `{frs_id}` or a field name is missing
- **THEN** the loader raises a `ValueError` naming the key
