## ADDED Requirements

### Requirement: Resolve CAS number to DTXSID
The system SHALL resolve a CAS registry number to a DSSTox substance identifier (DTXSID) by querying CompTox's exact CAS search, and SHALL accept a result only if CompTox reports it as a CAS-number match whose CAS equals the requested one. The CAS number SHALL be validated (format and check digit) and normalized to its hyphenated form before any request.

#### Scenario: Known CAS number
- **WHEN** CompTox returns a CAS-number match whose CAS equals the requested CAS
- **THEN** the system uses the DTXSID of that match for the property request

#### Scenario: Hyphens omitted
- **WHEN** the CAS number is given without hyphens, e.g. "71432"
- **THEN** it is looked up as "71-43-2"

#### Scenario: Match of another kind
- **WHEN** CompTox returns a result that is not a CAS-number match, or whose CAS differs from the one requested
- **THEN** the result is ignored and the system returns no properties

#### Scenario: Invalid CAS number
- **WHEN** the input is not a valid CAS number (wrong format or check digit)
- **THEN** the system returns no properties without contacting CompTox

#### Scenario: No match
- **WHEN** CompTox reports that no chemical matches the CAS number
- **THEN** the system returns no properties and does not raise

#### Scenario: Blank input
- **WHEN** the CAS number is empty or whitespace
- **THEN** the system returns no properties without contacting CompTox

### Requirement: Provide the chemical's molecular weight
The system SHALL return the molecular weight that CompTox's chemical detail holds for the DTXSID of a verified CAS match, reading the configured response field and reporting it in the configured unit, and SHALL return no value when CompTox gives none or gives something that is not a finite number.

#### Scenario: Molecular weight present
- **WHEN** the chemical detail carries a value in the configured field
- **THEN** that number is returned for the CAS number

#### Scenario: Not available
- **WHEN** the detail has no value in the configured field, a non-numeric one, or a non-finite one
- **THEN** no value is returned and nothing is raised

#### Scenario: One CAS search
- **WHEN** molecular weight, properties and toxicity values are all requested for one CAS number
- **THEN** the CAS search is sent once

### Requirement: Treat service responses as untrusted
The system SHALL check the type and shape of every CompTox field it uses before using it, and SHALL ignore any value that is missing, of the wrong type, not a finite number, or from a record that does not belong to the requested chemical, rather than guess or coerce it.

#### Scenario: Unexpected shape
- **WHEN** a response is not a list, an entry is not an object, or a used field has the wrong type
- **THEN** that data is ignored and no partial or coerced value is returned

#### Scenario: Non-finite number
- **WHEN** a numeric field is NaN or infinite
- **THEN** it is treated as absent

#### Scenario: Record for another chemical
- **WHEN** a ToxVal record's DTXSID differs from the one requested
- **THEN** the record is ignored

## MODIFIED Requirements

### Requirement: Resilient to service failures
The system SHALL return no properties, rather than raise, when CompTox is unreachable, times out, or answers with an error status or malformed body. A definitive "no match" answer (an empty result, HTTP 404, or HTTP 400 stating that zero results were found) MAY be cached; transient failures SHALL NOT be cached.

#### Scenario: Network failure
- **WHEN** a request fails or times out
- **THEN** no properties are returned and a later call for the same input contacts CompTox again

#### Scenario: Repeat lookup
- **WHEN** the same CAS number is looked up again after a successful lookup
- **THEN** the cached result is returned without contacting CompTox

#### Scenario: Zero-results answer
- **WHEN** CompTox answers HTTP 400 stating that zero results were found for the CAS number
- **THEN** it is treated as "no match", not as a transient failure

## REMOVED Requirements

### Requirement: Resolve SMILES to DTXSID
**Reason**: CompTox's by-SMILES search returns an unrelated compound for aromatic SMILES (benzene and toluene were verified live), so data for the wrong chemical was reported.
**Migration**: Look up by CAS number; see "Resolve CAS number to DTXSID".
