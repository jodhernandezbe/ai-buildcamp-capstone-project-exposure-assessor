## ADDED Requirements

### Requirement: Population settings
The system SHALL read from a `[population]` table: the tract service URL, layer and the field names used; the Census Data API base URL, ACS vintage year, dataset path and variable codes for the total, under-5, under-18 and 65-and-over counts; the name of the environment variable holding the Census API key (never the key itself); the default, minimum and maximum radius in kilometres; the maximum number of county requests; the request delay, timeout, retries and backoff; and the screening default (residents per square kilometre and the four age-band percentages), validated on load, and SHALL NOT embed them in Python code.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the population settings
- **THEN** it returns the values from the file

#### Scenario: Changing the vintage
- **WHEN** the ACS year is edited
- **THEN** subsequent lookups use it with no code change

#### Scenario: Key variable name only
- **WHEN** the settings are read
- **THEN** they expose the environment variable name, not a key value

#### Scenario: Invalid entry
- **WHEN** a key is missing, a number is negative, non-numeric or a boolean, the minimum radius exceeds the default or the default exceeds the maximum, the screening age bands do not sum to 100 within 0.5, or a variable code is empty
- **THEN** the loader raises a `ValueError` naming the offending key
