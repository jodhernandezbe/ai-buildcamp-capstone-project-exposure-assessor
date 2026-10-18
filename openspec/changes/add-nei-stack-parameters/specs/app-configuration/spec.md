## ADDED Requirements

### Requirement: Shared Envirofacts settings
The system SHALL read the Envirofacts base URL, delay between requests, request timeout, maximum retries and retry backoff from an `[efservice]` table, validated on load, and SHALL read the FRS-to-EIS query (path template containing `{frs_id}`, program name and the response field names) from a `[frs]` table.

#### Scenario: Loaded
- **WHEN** the loaders are asked for the Envirofacts and FRS settings
- **THEN** they return the values from the file

#### Scenario: Invalid entry
- **WHEN** a key is missing, a number is negative, non-numeric or a boolean, a timeout is zero, or the FRS path lacks `{frs_id}`
- **THEN** the loader raises a `ValueError` naming the key

### Requirement: NEI stack table settings
The system SHALL read from a `[stack.nei]` table: the shard directory, the shard filename template (containing `{prefix}`), the number of leading ID digits that name a shard, the ID column, the columns holding stack height, stack diameter, exit velocity and exit temperature, the unit each is reported in, the maximum number of candidates, the number of significant digits used to merge near-identical candidates, the raw NEI file location and the raw column names, and SHALL NOT embed them in Python code. Plausible ranges and target units SHALL be the ones configured for stack parameters. A relative path SHALL be resolved against the project root.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the stack settings
- **THEN** it returns the NEI shard location, column mapping, reported units, candidate cap and merge precision

#### Scenario: Changing a column or unit
- **WHEN** a column name or reported unit is edited
- **THEN** subsequent lookups use it with no code change

#### Scenario: Invalid NEI entry
- **WHEN** a key is missing, a unit is not a string, the filename template lacks `{prefix}`, the prefix digits or candidate cap is not a positive integer, or the merge precision is not between 1 and 15
- **THEN** the loader raises a `ValueError` naming the offending key

## MODIFIED Requirements

### Requirement: Externalized TRI settings
The system SHALL read the EPA Envirofacts TRI release-query path template, page size, maximum pages, and the list of environmental media to keep from the configuration file, and SHALL NOT embed them in Python code; the base URL, delay between requests, request timeout, maximum retries and retry backoff come from the shared `[efservice]` table. The configuration SHALL also name the TRI field names used for the kept records so a renamed column needs only a configuration change, and the list of states whose longitudes are east of Greenwich. The configuration SHALL also hold the operating hours per year used to turn an annual release into a rate (an `[emissions]` table, default 8,760), validated on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the TRI settings
- **THEN** it returns the path template, paging values and the media list from the file

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
- **WHEN** the page size or page cap is not a positive integer, the media list is empty, or the path lacks the CAS placeholder
- **THEN** the loader raises a `ValueError` naming the offending key
