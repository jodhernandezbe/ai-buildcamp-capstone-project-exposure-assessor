## Purpose

Keeps external-service URLs, endpoints and timing parameters in a configuration file
so they can change without editing code.

## ADDED Requirements

### Requirement: Externalized service settings
The system SHALL read the PubChem base URL, endpoint path template, request delay and
request timeout from a configuration file, and SHALL NOT embed them in Python code.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the PubChem settings
- **THEN** it returns the base URL, endpoint template, delay and timeout from the file

#### Scenario: Changing the endpoint
- **WHEN** the URL in the configuration file is edited
- **THEN** subsequent lookups use the new URL with no code change

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
