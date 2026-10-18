## ADDED Requirements

### Requirement: Meteorology settings
The system SHALL read from a `[meteorology]` table: the archive base URL and path, the hourly variable names requested, the wind speed unit requested, the delay between requests, the request timeout, the maximum retries and the retry backoff, the default reporting year, the first available year and the number of days the archive lags behind the present, the minimum wind speed, the wind direction sector width, and the screening default (wind speed, direction, stability class, temperature), validated on load, and SHALL NOT embed them in Python code.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the meteorology settings
- **THEN** it returns the values from the file

#### Scenario: Changing the archive or the default year
- **WHEN** the base URL or the default year is edited
- **THEN** subsequent lookups use it with no code change

#### Scenario: Invalid entry
- **WHEN** a key is missing, a number is negative, non-numeric or a boolean, a timeout is zero, the sector width does not divide 360 evenly, the first available year is later than the default year, or the screening default has a stability class outside A to F or a wind direction outside 0 to 360
- **THEN** the loader raises a `ValueError` naming the offending key
