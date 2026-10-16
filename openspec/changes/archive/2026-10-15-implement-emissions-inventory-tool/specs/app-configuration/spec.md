## ADDED Requirements

### Requirement: Externalized TRI settings
The system SHALL read the EPA Envirofacts TRI base URL, the release-query path template, page size, delay between requests, request timeout, maximum retries, retry backoff, maximum pages, and the list of environmental media to keep from the configuration file, and SHALL NOT embed them in Python code. The configuration SHALL also name the TRI field names used for the kept records so a renamed column needs only a configuration change, and the list of states whose longitudes are east of Greenwich. The configuration SHALL also hold the operating hours per year used to turn an annual release into a rate (an `[emissions]` table, default 8,760), validated on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the TRI settings
- **THEN** it returns the base URL, path template, paging, timing and retry values, and the media list from the file

#### Scenario: Changing the media
- **WHEN** a medium is added to or removed from the configured list
- **THEN** subsequent lookups use the new list with no code change

#### Scenario: Operating hours loaded
- **WHEN** the loader is asked for the emissions settings
- **THEN** it returns the operating hours per year from the file, and the unit alias table includes the TRI mass spelling "Pounds"

#### Scenario: Invalid operating hours
- **WHEN** the operating hours per year are missing, non-numeric, a boolean, zero, negative, or greater than 8,784
- **THEN** the loader raises a `ValueError` naming the key

#### Scenario: Invalid value
- **WHEN** the page size or page cap is not a positive integer, the delay, timeout or backoff is negative or non-numeric, the retries are negative, the media list is empty, or the path lacks the CAS placeholder
- **THEN** the loader raises a `ValueError` naming the offending key
