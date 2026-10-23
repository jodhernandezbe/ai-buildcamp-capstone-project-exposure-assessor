## Purpose

Resolves a chemical given as a CAS number, a SMILES or a name to its PubChem compound (CID) and retrieves its PubChem record, checking that the match really is the chemical asked for.

## ADDED Requirements

### Requirement: Detect the kind of identifier
The system SHALL classify a free-text identifier as a CAS number, a SMILES or a chemical name, in that order: a valid CAS registry number (including its check digit) is a CAS number; otherwise a string RDKit can parse is a SMILES; anything else is a name. The result SHALL state which kind was used, and the caller MAY state the kind to skip detection.

#### Scenario: CAS number
- **WHEN** the identifier is `106-97-8`
- **THEN** it is treated as a CAS number

#### Scenario: SMILES
- **WHEN** the identifier is `CCCC`
- **THEN** it is treated as a SMILES

#### Scenario: Name
- **WHEN** the identifier is `n-hexane`
- **THEN** it is treated as a name

#### Scenario: Invalid CAS check digit
- **WHEN** the identifier looks like a CAS number but its check digit is wrong and it is not a parsable SMILES
- **THEN** it is not treated as a CAS number

#### Scenario: Caller states the kind
- **WHEN** the caller states the kind
- **THEN** that kind is used, so a name that is also a valid SMILES can be searched as a name

### Requirement: Validate and canonicalize SMILES before searching
The system SHALL parse every SMILES with RDKit and search PubChem with the canonical SMILES, percent-encoded in the URL. A SMILES RDKit cannot parse SHALL raise a `ValueError` naming it. An empty identifier SHALL raise a `ValueError`.

#### Scenario: Equivalent SMILES give the same search
- **WHEN** two spellings of one molecule are resolved
- **THEN** both are searched with the same canonical SMILES

#### Scenario: Malformed SMILES
- **WHEN** a SMILES is requested and RDKit cannot parse `C(C`
- **THEN** a `ValueError` is raised and PubChem is not called

#### Scenario: Characters that are special in a URL
- **WHEN** the canonical SMILES contains `/`, `#`, `\`, `(` or `=`
- **THEN** it reaches PubChem as a single path segment

#### Scenario: Empty identifier
- **WHEN** the identifier is empty or whitespace
- **THEN** a `ValueError` is raised and PubChem is not called

### Requirement: Discover the CID of a compound
The system SHALL return the integer CID for an identifier. It SHALL return no CID, with a reason, when PubChem has no such compound, answers with more than one distinct CID, or gives a CID that is not a positive integer (a boolean included). It SHALL NOT pick one of several.

#### Scenario: Single match
- **WHEN** PubChem answers with one CID
- **THEN** that CID is returned as an integer

#### Scenario: Not found
- **WHEN** PubChem answers 404
- **THEN** no CID is returned and the reason says the compound was not found

#### Scenario: Several matches
- **WHEN** PubChem answers with several CIDs
- **THEN** no CID is returned and the reason says the identifier is ambiguous

#### Scenario: Malformed answer
- **WHEN** the answer has no CID list, a non-list, or an invalid CID
- **THEN** no CID is returned and the reason says the answer was not understood

#### Scenario: Service unavailable
- **WHEN** PubChem cannot be reached after the configured retries
- **THEN** no CID is returned, the reason says so, and no exception reaches the caller

### Requirement: Fetch the record of a compound
The system SHALL fetch the PUG View record of a CID and return the decoded JSON object, or no record with a reason when the fetch fails or the body is not an object with a `Record`. A CID that is not a positive integer SHALL raise a `ValueError` without a request.

#### Scenario: Record available
- **WHEN** PubChem answers with a record
- **THEN** the decoded record is returned unchanged

#### Scenario: Record missing or malformed
- **WHEN** PubChem answers 404 or the body has no `Record`
- **THEN** no record is returned and a reason is given

#### Scenario: Invalid CID
- **WHEN** the CID is zero, negative or not an integer
- **THEN** a `ValueError` is raised and PubChem is not called

### Requirement: Confirm the match by CAS number
When a record was found for a CAS number, the system SHALL accept it only if the record lists that CAS number among its own CAS registry identifiers (read from the configured heading). A record that lists other CAS numbers only, or none, SHALL be rejected with a reason, and nothing SHALL be read from it.

#### Scenario: Record confirms the CAS number
- **WHEN** the record lists the requested CAS number
- **THEN** the record is accepted

#### Scenario: Record belongs to another chemical
- **WHEN** a name search for the CAS number returns a record that lists a different CAS number only
- **THEN** the record is rejected and the reason says the CAS number was not confirmed

#### Scenario: Record lists no CAS number
- **WHEN** the record has no CAS identifiers
- **THEN** the record is rejected as unconfirmed

#### Scenario: Other kinds of identifier
- **WHEN** the identifier was a SMILES or a name
- **THEN** no CAS confirmation is required
