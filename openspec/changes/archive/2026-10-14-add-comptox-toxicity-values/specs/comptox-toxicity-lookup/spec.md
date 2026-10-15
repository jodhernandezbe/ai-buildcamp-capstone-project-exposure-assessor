## Purpose

Provides screening-level toxicity values (reference dose, reference concentration, slope factor, inhalation unit risk) for a chemical from EPA's CompTox ToxVal records, starting from a canonical SMILES.

## ADDED Requirements

### Requirement: Extract configured toxicity values
The system SHALL return, for each toxicity value in the configured list, its numeric value, unit and source, taken from the CompTox ToxVal records of the chemical's DTXSID. Initially the list SHALL contain RfD, RfC, SF (also labeled OSF) and IUR.

#### Scenario: Values present
- **WHEN** the ToxVal records include numeric entries for configured toxicity types
- **THEN** the result has one entry per configured toxicity value that was found, keyed by its configured key, each with value, unit and source

#### Scenario: Value absent
- **WHEN** no record matches a configured toxicity value, or the matching records have no numeric value
- **THEN** that value is omitted and the others are still returned

#### Scenario: Other record types ignored
- **WHEN** the records include types not in the configured list (e.g. NOAEL, LOAEL)
- **THEN** they do not appear in the result

#### Scenario: Alternate labels
- **WHEN** a configured toxicity value lists several accepted labels (e.g. SF and OSF)
- **THEN** a record carrying any of them is treated as that value

#### Scenario: Extending the list
- **WHEN** a new toxicity value is added to the configured list
- **THEN** it is extracted on the next lookup with no code change

### Requirement: Select among multiple records by source priority
The system SHALL choose, when several records match one toxicity value, the record whose source ranks highest in the configured ordered source list; sources not in the list SHALL rank below all listed sources, and ties SHALL resolve to the first record returned by CompTox.

#### Scenario: Preferred source present
- **WHEN** records from a listed source and an unlisted source both match
- **THEN** the listed source's record is used and its source name is reported

#### Scenario: No listed source
- **WHEN** only unlisted sources match
- **THEN** the first matching record returned by CompTox is used

### Requirement: Report toxicity units as provided
The system SHALL return the unit string supplied by CompTox with each value and SHALL NOT convert units.

#### Scenario: Unit passthrough
- **WHEN** a record's unit is "mg/kg-day"
- **THEN** the result carries exactly that unit string

### Requirement: Shared lookup behavior
The toxicity lookup SHALL use the same authentication, structure-to-DTXSID resolution, failure handling and caching rules as the property lookup, and a chemical looked up for both properties and toxicity values SHALL be resolved to its DTXSID only once.

#### Scenario: Both lookups for one chemical
- **WHEN** properties and then toxicity values are requested for the same SMILES
- **THEN** the DTXSID search request is sent once

#### Scenario: Failure
- **WHEN** the ToxVal request fails, times out, or returns an error status or malformed body
- **THEN** no toxicity values are returned, nothing is raised, and a later call contacts CompTox again

#### Scenario: Missing API key
- **WHEN** the API-key environment variable is unset or blank
- **THEN** the system raises an error naming the variable, without contacting CompTox
