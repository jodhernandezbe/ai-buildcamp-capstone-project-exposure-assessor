# smiles-lookup Specification

## Purpose

Provides a CAS-number to canonical-SMILES resolution step so that downstream property
lookups can work from a chemical structure identifier.

## Requirements

### Requirement: Resolve CAS number to canonical SMILES
The system SHALL return the RDKit-canonical SMILES for a CAS registry number by querying PubChem.

#### Scenario: Known CAS number
- **WHEN** a valid CAS number that PubChem recognizes is looked up
- **THEN** the system returns a SMILES string that has been canonicalized by RDKit

#### Scenario: Unknown CAS number
- **WHEN** PubChem reports that no compound matches the CAS number
- **THEN** the system returns no SMILES (None) and does not raise

#### Scenario: Blank input
- **WHEN** the CAS number is empty or whitespace
- **THEN** the system returns no SMILES without contacting PubChem

### Requirement: Fall back across PubChem SMILES fields
The system SHALL use the first available of the SMILES fields PubChem returns for the compound.

#### Scenario: Preferred field missing
- **WHEN** the response lacks `CanonicalSMILES` but has `ConnectivitySMILES` or `SMILES`
- **THEN** the system uses the available field

#### Scenario: RDKit cannot parse the returned SMILES
- **WHEN** RDKit fails to parse the SMILES PubChem returned
- **THEN** the system returns PubChem's raw SMILES unchanged

### Requirement: Tolerate service failures
The system SHALL treat network errors, timeouts, non-success HTTP statuses and malformed
responses as "not found" and SHALL log them at debug level rather than raising.

#### Scenario: Network failure
- **WHEN** the request to PubChem times out or the connection fails
- **THEN** the system returns no SMILES

#### Scenario: Malformed response
- **WHEN** the response body is not the expected JSON structure
- **THEN** the system returns no SMILES

### Requirement: Cache lookups
The system SHALL cache results, including misses, keyed by the normalized CAS number
(whitespace and hyphens removed), so repeated lookups do not call PubChem again.

#### Scenario: Repeated lookup
- **WHEN** the same CAS number is looked up twice, in any hyphen/whitespace formatting
- **THEN** PubChem is contacted only once

### Requirement: Respect PubChem rate limits
The system SHALL wait the configured delay before each PubChem request.

#### Scenario: Configured delay
- **WHEN** a lookup misses the cache
- **THEN** the system waits the configured number of seconds before sending the request
