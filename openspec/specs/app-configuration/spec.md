# app-configuration Specification

## Purpose

Keeps external-service URLs, endpoints and timing parameters in a configuration file
so they can change without editing code.

## Requirements


### Requirement: Externalized service settings
The system SHALL read the CompTox base URL, endpoint path templates (CAS search, chemical detail, property summary and ToxVal), request delay and request timeout from a configuration file, and SHALL NOT embed them in Python code. The configuration SHALL also name the CompTox API-key header and the environment variable holding the key, SHALL name where molecular weight is read from (response field, the unit the service reports it in, target unit), SHALL list the CompTox properties to extract (CompTox property name, result key, target unit), and SHALL list the CompTox toxicity values to extract (result key, accepted ToxVal type labels, accepted exposure routes, preference for the lowest or highest value, target unit) together with the ordered source-priority list used to choose among records. The configuration SHALL also hold a table of unit-spelling aliases used before unit conversion.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the CompTox settings
- **THEN** it returns the base URL, endpoint templates, delay and timeout from the file, plus the header name, key variable name, property list, toxicity value list and source-priority list for CompTox, with a target unit on every property and toxicity entry and routes and preference on every toxicity entry

#### Scenario: Changing the endpoint
- **WHEN** the URL in the configuration file is edited
- **THEN** subsequent lookups use the new URL with no code change

#### Scenario: Adding a property
- **WHEN** an entry is added to the CompTox property list
- **THEN** the loader returns it with no code change

#### Scenario: Adding a toxicity value
- **WHEN** an entry is added to the CompTox toxicity value list
- **THEN** the loader returns it with no code change

#### Scenario: Invalid toxicity entry
- **WHEN** a toxicity entry has no key, no accepted labels, no accepted routes, a preference other than "lowest" or "highest", or a duplicate key
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Molecular weight settings
- **WHEN** the loader is asked for the CompTox settings
- **THEN** it returns the molecular weight response field, reported unit and target unit, and raises a `ValueError` naming the key if the table or any of its keys is missing

#### Scenario: Missing target unit
- **WHEN** a property or toxicity entry has no target unit
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: CAS search path without placeholder
- **WHEN** the CAS search path does not contain the CAS placeholder
- **THEN** the loader raises a `ValueError` naming the key

#### Scenario: Unit aliases loaded
- **WHEN** the loader is asked for the unit settings
- **THEN** it returns the alias table from the file, and a missing table yields no aliases

### Requirement: Validated, typed configuration
The system SHALL validate the configuration on load and expose it as typed objects.

#### Scenario: Missing or invalid value
- **WHEN** a required key is missing, or the delay or timeout is negative or non-numeric
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Missing file
- **WHEN** the configuration file does not exist
- **THEN** the loader raises `FileNotFoundError` naming the path

### Requirement: Overridable location
The system SHALL allow the configuration file path to be supplied explicitly, and
otherwise use the default file shipped in the repository.

#### Scenario: Explicit path
- **WHEN** a path is passed to the loader
- **THEN** that file is read instead of the default

### Requirement: Secrets kept out of configuration
The configuration file SHALL NOT contain API keys; it SHALL only name the environment variable that holds them.

#### Scenario: Key reference
- **WHEN** CompTox settings are loaded
- **THEN** they expose the environment variable name, not a key value

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

### Requirement: Stack parameter settings
The configuration SHALL hold, for the stack-parameter tools: the PSTK file path, its SCC column, an optional FIPS column with the values that mark national rows, the column and source unit of each of the four stack quantities, the target unit of each quantity, the plausible range (minimum and maximum, in target units) for each quantity, and the AirToxScreen global fallback values (3.0 m, 0.2 m, 4.0 m/s, 295.4 K). The loader SHALL return these as an immutable typed object.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the stack settings
- **THEN** it returns the PSTK path, column mapping, source and target units, plausible ranges and fallback values

#### Scenario: Invalid stack settings
- **WHEN** a fallback value is not a positive finite number, a range has minimum not below maximum, a fallback lies outside its range, or a quantity is missing from any table
- **THEN** the loader raises an error naming the offending entry

#### Scenario: Unconvertible source unit
- **WHEN** a configured source unit cannot be converted to its target unit
- **THEN** an error naming the quantity is raised before any lookup result is returned

### Requirement: SCC index settings
The configuration SHALL hold, for the SCC retrieval tool: the source table path, its column names, the persisted index directory, the collection name, the data categories and statuses to index, the number of results to return and the indexing batch size. It SHALL separately hold the embedding settings: provider name, model name, API-key environment variable name and request timeout. The loaders SHALL return these as immutable typed objects.

#### Scenario: Settings loaded
- **WHEN** the loaders are asked for the SCC index and embedding settings
- **THEN** they return every listed value from the file

#### Scenario: Invalid SCC index settings
- **WHEN** the result count, batch size or timeout is not a positive number, the category or status list is empty, a column name is missing, the provider is not a supported one, or the model name or collection name is blank
- **THEN** the loader raises an error naming the offending entry

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
