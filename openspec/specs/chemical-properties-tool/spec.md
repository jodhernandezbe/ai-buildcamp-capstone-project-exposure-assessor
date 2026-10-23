# chemical-properties-tool Specification

## Purpose
Gives the agent one tool that turns a CAS number into the physical-chemical and toxicity inputs the exposure and risk steps need, in fixed units, with clear signals when something is missing.

## Requirements

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

### Requirement: Fixed output units
The tool SHALL return every value in its documented unit, converting from the unit the source reports: molecular weight in g/mol, vapor pressure in mmHg, density in g/cm^3, RfD in mg/(kg*day), RfC in mg/m^3, SF in (mg/(kg*day))^-1 and IUR in (ug/m^3)^-1. The target units SHALL come from configuration.

#### Scenario: Source in a different unit
- **WHEN** a source reports RfC in "ug/m3"
- **THEN** the returned RfC is the converted number in mg/m^3

#### Scenario: Changing a target unit
- **WHEN** a target unit is edited in configuration
- **THEN** subsequent results use the new unit with no code change

### Requirement: Dimensionality guardrail
The tool SHALL NOT return a value whose unit could not be converted to the target unit.

#### Scenario: Incompatible unit
- **WHEN** a source reports a value in a unit of a different dimension than the target
- **THEN** that field is None and a warning names the field, the reported unit and the target unit

#### Scenario: Unknown unit
- **WHEN** a source reports a unit the converter does not recognize
- **THEN** that field is None and a warning names the field and the unit

### Requirement: Missing values are explicit
The tool SHALL return every field on every call, using None for values it could not obtain, and SHALL explain each missing value in a warnings list.

#### Scenario: Value not in any source
- **WHEN** CompTox has no IUR for the chemical
- **THEN** the iur field is None and a warning says it was not found

#### Scenario: Data service failure
- **WHEN** a CompTox request fails
- **THEN** the affected fields are None, a warning says no CompTox data was retrieved (not found or service unavailable), and the tool does not raise

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

### Requirement: Missing API key is a setup error
The tool SHALL raise an error naming the missing environment variable when the CompTox API key is not set and the CAS number is valid, rather than report it as missing data.

#### Scenario: Key unset
- **WHEN** the CompTox key variable is unset and the CAS number is valid
- **THEN** the tool raises an error naming the variable

#### Scenario: Invalid CAS number with no key
- **WHEN** the CAS number is invalid and the key is unset
- **THEN** the tool returns the unresolved result without raising

### Requirement: Self-describing for the model
The tool's description SHALL state each field, its unit and the meaning of None, warnings and sources, so the agent can use and relay them correctly, and SHALL say that `preferred_name` is the only name to call the chemical by, and that a chemical whose name is None is referred to by its CAS number alone.

#### Scenario: Tool schema
- **WHEN** the tool is registered
- **THEN** it takes a single `cas_number` argument and has a description listing the fields with units, the name among them

### Requirement: Molecular weight in g/mol from CompTox
The tool SHALL report molecular weight in g/mol as held by CompTox for the chemical, reading it from the configured response field and converting it from the configured reported unit to the configured target unit like every other value, and SHALL NOT calculate it.

#### Scenario: Available
- **WHEN** CompTox has a molecular weight for the chemical
- **THEN** molecular weight is that number in g/mol and its source is "CompTox"

#### Scenario: Reported in another unit
- **WHEN** the configured reported unit differs from the target unit (e.g. kg/mol)
- **THEN** the returned value is converted to the target unit

#### Scenario: Incompatible unit
- **WHEN** the configured reported unit cannot be converted to the target unit
- **THEN** molecular weight is None and a warning names the units

### Requirement: Toxicity context for explanations
The tool SHALL return, for every RfD, RfC, SF and IUR that has a value, the database it came from, the exposure route the value applies to (oral for RfD and SF, inhalation for RfC and IUR, taken from configuration), the route as the source recorded it ("not specified" when the source gave none), the critical effect or cancer endpoint, and whether it is a cancer or non-cancer value, and SHALL tell the model in its description to report them. Values that are None SHALL have no entry.

#### Scenario: Cancer value
- **WHEN** the slope factor comes from a record whose effect is "leukemia"
- **THEN** its entry names the source, the oral route, and the endpoint "leukemia" with a cancer assessment

#### Scenario: Route not stated by the source
- **WHEN** a reference concentration comes from a source that records no route
- **THEN** its entry shows inhalation as the applied route and "not specified" as the reported route

#### Scenario: Value missing or rejected
- **WHEN** a toxicity value is None
- **THEN** no entry exists for it

#### Scenario: Description
- **WHEN** the tool is registered
- **THEN** its description explains these fields and asks the model to state route, source and endpoint when reporting a toxicity value

### Requirement: Plausibility guard
The tool SHALL return None, with a warning naming the field and the value, for any converted value that is not a finite number greater than zero, since every returned quantity is physically positive and the risk calculations divide by or multiply with it.

#### Scenario: Zero or negative value
- **WHEN** a source reports a reference concentration of 0 or a negative number
- **THEN** rfc is None and a warning says the value was rejected

#### Scenario: Non-finite after conversion
- **WHEN** a conversion produces infinity or NaN
- **THEN** that field is None and a warning says so

### Requirement: Inputs and outputs are never shared or mutated
The tool SHALL NOT let a caller alter cached results or configuration by modifying a returned value.

#### Scenario: Caller mutates the result
- **WHEN** a caller modifies the returned `sources` or `warnings`
- **THEN** a later call for the same CAS number is unaffected

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
