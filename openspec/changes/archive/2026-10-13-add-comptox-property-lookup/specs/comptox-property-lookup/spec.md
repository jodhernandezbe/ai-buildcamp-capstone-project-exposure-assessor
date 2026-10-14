## Purpose

Provides screening-level physical-chemical property values (initially vapor pressure and density) for a chemical from EPA's CompTox Chemicals Dashboard, starting from a canonical SMILES.

## ADDED Requirements

### Requirement: Resolve SMILES to DTXSID
The system SHALL resolve a canonical SMILES to a DSSTox substance identifier (DTXSID) by querying CompTox.

#### Scenario: Known structure
- **WHEN** CompTox returns a match for the SMILES
- **THEN** the system uses the DTXSID of the match for the property request

#### Scenario: No match
- **WHEN** CompTox returns no match for the SMILES
- **THEN** the system returns no properties and does not raise

#### Scenario: Blank input
- **WHEN** the SMILES is empty or whitespace
- **THEN** the system returns no properties without contacting CompTox

### Requirement: Extract configured properties
The system SHALL return, for each property named in the configured property list, its value, unit and source, taken from the CompTox property summary for the DTXSID. Initially the list SHALL contain vapor pressure and density.

#### Scenario: Properties present
- **WHEN** the summary contains entries for all configured properties
- **THEN** the result has one entry per configured property, keyed by the configured key, each with value, unit and source

#### Scenario: Property absent from summary
- **WHEN** a configured property has no entry, or has no experimental or predicted value
- **THEN** that property is omitted from the result and the others are still returned

#### Scenario: Unconfigured properties ignored
- **WHEN** the summary contains properties not in the configured list
- **THEN** they do not appear in the result

#### Scenario: Extending the list
- **WHEN** a new property is added to the configured list
- **THEN** it is extracted on the next lookup with no code change

### Requirement: Prefer experimental over predicted
The system SHALL use the experimental median when it is available, and otherwise the predicted median, and SHALL report which was used.

#### Scenario: Experimental available
- **WHEN** both experimental and predicted medians exist
- **THEN** the value is the experimental median and the source is "experimental"

#### Scenario: Only predicted available
- **WHEN** the experimental median is null and the predicted median exists
- **THEN** the value is the predicted median and the source is "predicted"

### Requirement: Report units as provided
The system SHALL return the unit string supplied by CompTox with each value and SHALL NOT convert units.

#### Scenario: Unit passthrough
- **WHEN** CompTox reports vapor pressure in "mmHg" and density in "g/cm^3"
- **THEN** the result carries those exact unit strings

### Requirement: Authenticated requests
The system SHALL send the CompTox API key, read from the environment, with every request, and SHALL NOT store the key in code or configuration files.

#### Scenario: Key available
- **WHEN** the configured environment variable is set
- **THEN** its value is sent in the configured API-key header

#### Scenario: Key missing
- **WHEN** the configured environment variable is unset or blank
- **THEN** the system raises an error naming the variable, without contacting CompTox

### Requirement: Resilient to service failures
The system SHALL return no properties, rather than raise, when CompTox is unreachable, times out, or answers with an error status or malformed body. Definitive "no match" answers MAY be cached; transient failures SHALL NOT be cached.

#### Scenario: Network failure
- **WHEN** a request fails or times out
- **THEN** no properties are returned and a later call for the same input contacts CompTox again

#### Scenario: Repeat lookup
- **WHEN** the same SMILES is looked up again after a successful lookup
- **THEN** the cached result is returned without contacting CompTox
