## ADDED Requirements

### Requirement: User-supplied property values
The tool SHALL accept, for each chemical property field, a value the user supplied in the
documented target unit (after conversion and validation by the caller), and SHALL report a
user-supplied value in place of a missing one. The tool SHALL NOT replace a value that was found
in CompTox or PubChem with a user-supplied one: confirmation requests only ask for values that
are missing.

#### Scenario: Supplied value fills a gap
- **WHEN** CompTox and PubChem have no vapor pressure and the user supplied one
- **THEN** the vapor pressure field is the supplied value, its sources entry is "user-provided", and no warning says it is missing

#### Scenario: Found value is kept
- **WHEN** CompTox has a density and the user supplies a different density without a confirmation request for it
- **THEN** the CompTox density is kept and the supplied value is not used

#### Scenario: Declined value stays missing
- **WHEN** the user proceeds without a value that has no source
- **THEN** the field stays None and its warning is kept

### Requirement: Provenance includes user-provided
The provenance report for chemical properties SHALL include "user-provided" as a source for a
field whose value came from the user, alongside the existing sources.

#### Scenario: Provenance label
- **WHEN** a field was supplied by the user
- **THEN** its sources entry reads "user-provided"
