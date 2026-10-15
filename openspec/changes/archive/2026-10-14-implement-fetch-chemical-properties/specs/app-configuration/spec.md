## MODIFIED Requirements

### Requirement: Externalized service settings
The system SHALL read the PubChem and CompTox base URLs, endpoint path templates, request delay and request timeout from a configuration file, and SHALL NOT embed them in Python code. The configuration SHALL also name the CompTox API-key header and the environment variable holding the key, SHALL list the CompTox properties to extract (CompTox property name, result key, target unit), and SHALL list the CompTox toxicity values to extract (result key, accepted ToxVal type labels, target unit) together with the ordered source-priority list used to choose among records. The configuration SHALL also hold a table of unit-spelling aliases used before unit conversion.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the PubChem or CompTox settings
- **THEN** it returns the base URL, endpoint templates, delay and timeout from the file, plus the header name, key variable name, property list, toxicity value list and source-priority list for CompTox, with a target unit on every property and toxicity entry

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
- **WHEN** a toxicity entry has no key, no accepted labels, or a duplicate key
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Missing target unit
- **WHEN** a property or toxicity entry has no target unit
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Unit aliases loaded
- **WHEN** the loader is asked for the unit settings
- **THEN** it returns the alias table from the file, and a missing table yields no aliases
