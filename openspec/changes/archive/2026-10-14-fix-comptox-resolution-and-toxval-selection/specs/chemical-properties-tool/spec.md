## MODIFIED Requirements

### Requirement: Resolve a chemical and return its properties
The tool SHALL accept a CAS registry number and return the molecular weight, vapor pressure, density, RfD, RfC, SF and IUR of the chemical, using CompTox as its only data service. All data SHALL be looked up by the CAS number directly.

#### Scenario: Known chemical
- **WHEN** the CAS number is known to CompTox
- **THEN** each field with data carries a number in its documented unit

#### Scenario: Molecular weight unavailable
- **WHEN** CompTox knows the CAS number but has no molecular weight for it, as for some mixtures
- **THEN** the other fields are returned, molecular weight is None, and a warning says why

#### Scenario: CompTox has no property or toxicity data
- **WHEN** CompTox knows the CAS number but has no property or toxicity data
- **THEN** molecular weight is returned if available, the other fields are None, and a warning says no CompTox data was retrieved

#### Scenario: Unresolvable CAS number
- **WHEN** the CAS number is blank, invalid, or unknown to CompTox
- **THEN** every field is None and a warning says the CAS number could not be resolved

### Requirement: Provenance of values
The tool SHALL report, for each field that has a value, where it came from: "CompTox" for molecular weight, "experimental" or "predicted" for properties, and the ToxVal source name for toxicity values.

#### Scenario: Experimental value
- **WHEN** vapor pressure comes from an experimental median
- **THEN** the sources entry for vapor pressure is "experimental"

#### Scenario: Molecular weight
- **WHEN** molecular weight is returned
- **THEN** the sources entry for molecular weight is "CompTox"

### Requirement: Missing API key is a setup error
The tool SHALL raise an error naming the missing environment variable when the CompTox API key is not set and the CAS number is valid, rather than report it as missing data.

#### Scenario: Key unset
- **WHEN** the CompTox key variable is unset and the CAS number is valid
- **THEN** the tool raises an error naming the variable

#### Scenario: Invalid CAS number with no key
- **WHEN** the CAS number is invalid and the key is unset
- **THEN** the tool returns the unresolved result without raising

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Molecular weight from the structure
**Reason**: Molecular weight is no longer calculated from a structure; CompTox supplies it directly, so RDKit and the structure lookup are gone.
**Migration**: See "Molecular weight in g/mol from CompTox".
