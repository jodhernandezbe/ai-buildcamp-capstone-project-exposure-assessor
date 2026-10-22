## MODIFIED Requirements

### Requirement: Resolve a chemical and return its properties
The tool SHALL accept a CAS registry number and return the chemical's preferred name, molecular weight, vapor pressure, density, RfD, RfC, SF and IUR, using CompTox as its only data service. All data SHALL be looked up by the CAS number directly. The name SHALL be the one CompTox reports for the CAS-number match, never one supplied by the tool itself.

#### Scenario: Known chemical
- **WHEN** the CAS number is known to CompTox
- **THEN** each field with data carries a number in its documented unit, and the preferred name is the text CompTox gave with its source "CompTox"

#### Scenario: Name missing
- **WHEN** CompTox's match carries no usable name
- **THEN** the preferred name is None and a warning says so; the other fields are unaffected

#### Scenario: Molecular weight unavailable
- **WHEN** CompTox knows the CAS number but has no molecular weight for it, as for some mixtures
- **THEN** the other fields are returned, molecular weight is None, and a warning says why

#### Scenario: CompTox has no property or toxicity data
- **WHEN** CompTox knows the CAS number but has no property or toxicity data
- **THEN** the name and molecular weight are returned if available, the other fields are None, and a warning says no CompTox data was retrieved

#### Scenario: Unresolvable CAS number
- **WHEN** the CAS number is blank, invalid, or unknown to CompTox
- **THEN** every field, the name included, is None and a warning says the CAS number could not be resolved

### Requirement: Self-describing for the model
The tool's description SHALL state each field, its unit and the meaning of None, warnings and sources, so the agent can use and relay them correctly, and SHALL say that `preferred_name` is the only name to call the chemical by, and that a chemical whose name is None is referred to by its CAS number alone.

#### Scenario: Tool schema
- **WHEN** the tool is registered
- **THEN** it takes a single `cas_number` argument and has a description listing the fields with units, the name among them
