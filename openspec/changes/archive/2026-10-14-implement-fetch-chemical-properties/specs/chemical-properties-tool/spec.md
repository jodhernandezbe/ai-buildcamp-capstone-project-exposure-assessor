## Purpose

Gives the agent one tool that turns a CAS number into the physical-chemical and toxicity inputs the exposure and risk steps need, in fixed units, with clear signals when something is missing.

## ADDED Requirements

### Requirement: Resolve a chemical and return its properties
The tool SHALL accept a CAS registry number and return the molecular weight, vapor pressure, density, RfD, RfC, SF and IUR of the chemical.

#### Scenario: Known chemical
- **WHEN** the CAS number resolves to a structure and the data sources have values
- **THEN** each field carries a number in its documented unit

#### Scenario: Unresolvable CAS number
- **WHEN** the CAS number cannot be resolved to a structure, or is blank
- **THEN** every field is None and a warning says the CAS number could not be resolved

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
The tool SHALL report, for each field that has a value, where it came from: "calculated" for molecular weight, "experimental" or "predicted" for properties, and the ToxVal source name for toxicity values.

#### Scenario: Experimental value
- **WHEN** vapor pressure comes from an experimental median
- **THEN** the sources entry for vapor pressure is "experimental"

### Requirement: Molecular weight from the structure
The tool SHALL compute molecular weight in g/mol from the resolved structure rather than look it up.

#### Scenario: Structure available
- **WHEN** the CAS number resolves to a structure
- **THEN** molecular weight is the structure's average molecular mass in g/mol

### Requirement: Missing API key is a setup error
The tool SHALL raise an error naming the missing environment variable when the CompTox API key is not set, rather than report it as missing data.

#### Scenario: Key unset
- **WHEN** the CompTox key variable is unset and a CAS number resolves to a structure
- **THEN** the tool raises an error naming the variable

### Requirement: Self-describing for the model
The tool's description SHALL state each field, its unit and the meaning of None, warnings and sources, so the agent can use and relay them correctly.

#### Scenario: Tool schema
- **WHEN** the tool is registered
- **THEN** it takes a single `cas_number` argument and has a description listing the fields with units
