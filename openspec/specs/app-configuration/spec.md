# app-configuration Specification

## Purpose

Keeps external-service URLs, endpoints and timing parameters in a configuration file
so they can change without editing code.

## Requirements

### Requirement: Externalized service settings
The system SHALL read the PubChem and CompTox base URLs, endpoint path templates, request delay and request timeout from a configuration file, and SHALL NOT embed them in Python code. The configuration SHALL also name the CompTox API-key header and the environment variable holding the key, and SHALL list the CompTox properties to extract (CompTox property name, result key).

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the PubChem or CompTox settings
- **THEN** it returns the base URL, endpoint templates, delay and timeout from the file, plus the header name, key variable name and property list for CompTox

#### Scenario: Changing the endpoint
- **WHEN** the URL in the configuration file is edited
- **THEN** subsequent lookups use the new URL with no code change

#### Scenario: Adding a property
- **WHEN** an entry is added to the CompTox property list
- **THEN** the loader returns it with no code change

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
