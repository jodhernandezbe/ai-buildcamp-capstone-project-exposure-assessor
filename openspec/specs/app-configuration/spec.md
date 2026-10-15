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
