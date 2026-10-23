## MODIFIED Requirements

### Requirement: Resolve a chemical and return its properties
The tool SHALL accept a CAS registry number and return the chemical's preferred name, molecular weight, vapor pressure, density, RfD, RfC, SF and IUR. CompTox SHALL be the primary data service; PubChem SHALL be used only as a fallback for the fields the PubChem configuration lists and only for fields CompTox left None. All data SHALL be looked up by the CAS number directly. The name SHALL be the one CompTox reports for the CAS-number match, never one supplied by the tool itself or by PubChem.

#### Scenario: Known chemical
- **WHEN** the CAS number is known to CompTox
- **THEN** each field with data carries a number in its documented unit, and the preferred name is the text CompTox gave with its source "CompTox"

#### Scenario: Name missing
- **WHEN** CompTox's match carries no usable name
- **THEN** the preferred name is None and a warning says so, even when PubChem knows the chemical; the other fields are unaffected

#### Scenario: Molecular weight unavailable
- **WHEN** CompTox knows the CAS number but has no molecular weight for it and PubChem gives none either
- **THEN** the other fields are returned, molecular weight is None, and a warning says why

#### Scenario: CompTox has no property or toxicity data
- **WHEN** CompTox knows the CAS number but has no property or toxicity data
- **THEN** the name and molecular weight are returned if available, PubChem is tried for the missing configured fields, the other fields stay None, and a warning says no CompTox data was retrieved

#### Scenario: Unresolvable CAS number
- **WHEN** the CAS number is blank or invalid
- **THEN** every field, the name included, is None, a warning says the CAS number could not be resolved, and PubChem is not called

#### Scenario: CAS number unknown to CompTox but known to PubChem
- **WHEN** CompTox does not know a valid CAS number and PubChem has a record that confirms it
- **THEN** the configured fields PubChem could give are returned with source "PubChem", the name and the toxicity values are None, and a warning says CompTox did not resolve the CAS number

### Requirement: Provenance of values
The tool SHALL report, for each field that has a value, where it came from: "CompTox" for molecular weight, "experimental" or "predicted" for CompTox properties, the ToxVal source name for toxicity values, and "PubChem" for any value taken from PubChem.

#### Scenario: Experimental value
- **WHEN** vapor pressure comes from a CompTox experimental median
- **THEN** the sources entry for vapor pressure is "experimental"

#### Scenario: Molecular weight
- **WHEN** molecular weight comes from CompTox
- **THEN** the sources entry for molecular weight is "CompTox"

#### Scenario: Value from PubChem
- **WHEN** a field was filled from PubChem
- **THEN** its sources entry is "PubChem" and a warning says CompTox had no value and PubChem's was used

#### Scenario: Model-facing description unchanged
- **WHEN** the tool is registered
- **THEN** its description is the one that does not mention PubChem, because the result already says where each value came from (the `sources` entry and the warning); wording about PubChem in the description made the full-assessment evaluation unstable

## ADDED Requirements

### Requirement: PubChem fills only gaps
The tool SHALL call PubChem only when a field the PubChem configuration lists is still None after CompTox, SHALL never replace or alter a value CompTox gave, and SHALL make no PubChem request when no listed field is missing.

#### Scenario: CompTox has everything
- **WHEN** CompTox gave molecular weight, vapor pressure and density
- **THEN** PubChem is not called

#### Scenario: One gap
- **WHEN** CompTox gave everything but density and PubChem has a clear density
- **THEN** only density comes from PubChem and the CompTox values are unchanged

#### Scenario: CompTox value rejected
- **WHEN** CompTox's vapor pressure failed validation and so is None
- **THEN** PubChem is tried for vapor pressure and the CompTox warning is kept

#### Scenario: Toxicity values
- **WHEN** CompTox has no RfC
- **THEN** rfc stays None, PubChem is not asked for it, and the warning says it was not found

### Requirement: PubChem values pass the same checks
A value from PubChem SHALL be converted to the field's documented unit and rejected unless it is a finite number greater than zero, exactly like a CompTox value, with a warning naming the field, the reported unit and the target unit when it is rejected.

#### Scenario: Unit conversion
- **WHEN** PubChem gives a density in `g/cu cm`
- **THEN** the returned density is the number in g/cm^3

#### Scenario: Incompatible unit
- **WHEN** PubChem gives a vapor pressure in a unit that is not a pressure
- **THEN** vapor pressure is None and a warning names the field and the units

### Requirement: PubChem failure never breaks the tool
The tool SHALL NOT raise because of PubChem. An unreachable service, a compound not found, an ambiguous or unconfirmed match, or a malformed record SHALL leave the affected fields as CompTox left them, with a warning saying why PubChem could not help. A missing CompTox key SHALL remain a setup error and SHALL NOT be bypassed through PubChem.

#### Scenario: PubChem down
- **WHEN** PubChem cannot be reached
- **THEN** the result equals the CompTox-only result plus a warning that PubChem could not be reached

#### Scenario: Unconfirmed match
- **WHEN** the PubChem record does not list the requested CAS number
- **THEN** no PubChem value is used and a warning says the match was not confirmed

#### Scenario: Key unset
- **WHEN** the CompTox key variable is unset and the CAS number is valid
- **THEN** the tool raises an error naming the variable, before any PubChem request
