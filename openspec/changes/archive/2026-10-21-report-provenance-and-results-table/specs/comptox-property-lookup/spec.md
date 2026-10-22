## MODIFIED Requirements

### Requirement: Resolve CAS number to DTXSID
The system SHALL resolve a CAS registry number to a DSSTox substance identifier (DTXSID) by querying CompTox's exact CAS search, and SHALL accept a result only if CompTox reports it as a CAS-number match whose CAS equals the requested one. The accepted match's preferred name SHALL be kept with the DTXSID when it is a non-empty string, and left absent otherwise (a missing name never rejects the match). The CAS number SHALL be validated (format and check digit) and normalized to its hyphenated form before any request.

#### Scenario: Known CAS number
- **WHEN** CompTox returns a CAS-number match whose CAS equals the requested CAS
- **THEN** the system uses the DTXSID of that match for the property request and keeps its preferred name

#### Scenario: Name absent or not text
- **WHEN** the accepted match has no preferred name, or it is blank or not a string
- **THEN** the DTXSID is still used and the name is absent

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
