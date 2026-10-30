# pubchem-occupational-limits Specification

## Purpose

Reading the occupational exposure limits of a chemical from its PubChem record and choosing the 8-hour benchmark in mg/m^3.

## Requirements

### Requirement: Limits come from configured headings
The system SHALL read the OSHA permissible exposure limit, NIOSH recommended exposure limit (TWA), ACGIH threshold limit values (TWA and STEL), NIOSH IDLH and the protective action criteria (PAC-1, PAC-2, PAC-3) from the record headings named in the configuration (under "Safety and Hazards", "Exposure Control and Personal Protection"), in the same PUG View response already fetched, with no extra request. Adding a limit to the configuration SHALL make it extractable with no code change.

#### Scenario: Limits in the record
- **WHEN** the record has OSHA, NIOSH and ACGIH statements
- **THEN** a candidate is read for each

#### Scenario: No extra request
- **WHEN** a chemical's properties and limits are both wanted
- **THEN** one PUG View request serves both

#### Scenario: Missing section
- **WHEN** the record has no "Exposure Control and Personal Protection" section
- **THEN** every limit is null with the reason, and the properties are still returned

### Requirement: Clear statements and unit normalisation
The system SHALL accept a statement only when it gives exactly one number and one unit of ppm or of mass per volume (mg/m^3, mg/cu m, ug/m^3), the number is finite and greater than zero, and it is a time-weighted average for the TWA limits; ranges, inequalities, ceilings given as the only value, several numbers and "see appendix" text SHALL be skipped with a reason. A value in ppm SHALL be converted to mg/m^3 at 25 degC and 1 atm as ppm times molecular weight over 24.45 using the compound's molecular weight, and SHALL be skipped with a reason, never converted with a guessed weight, when no molecular weight is known. A value already in mass per volume SHALL be used as given, converted only by units.

#### Scenario: ppm with a molecular weight
- **WHEN** a statement reads 50 ppm and the molecular weight is 100 g/mol
- **THEN** the value is 50 x 100 over 24.45 mg/m^3

#### Scenario: ppm without a molecular weight
- **WHEN** a statement reads 50 ppm and no molecular weight was found
- **THEN** it is skipped and the reason says why

#### Scenario: Already mg/m^3
- **WHEN** a statement reads 5 mg/cu m
- **THEN** the value is 5 mg/m^3

#### Scenario: Ambiguous text
- **WHEN** a statement gives a range, an inequality or two numbers
- **THEN** it is skipped with a reason

### Requirement: Primary 8-hour benchmark with its source
The system SHALL choose the 8-hour TWA benchmark as the first available of OSHA PEL-TWA, NIOSH REL-TWA, ACGIH TLV-TWA, and return it as `oel_twa_mg_m3` with `oel_source` naming the programme and the PubChem record. When none is available both SHALL be null with a reason. Every other limit found SHALL be returned with its own source, not merged.

#### Scenario: OSHA wins
- **WHEN** OSHA, NIOSH and ACGIH values are all present
- **THEN** the benchmark is the OSHA value and the source says OSHA PEL

#### Scenario: Fallback
- **WHEN** only the ACGIH value is present
- **THEN** the benchmark is the ACGIH value and the source says ACGIH TLV

#### Scenario: None
- **WHEN** no TWA limit is present
- **THEN** the benchmark and its source are null with a reason, and IDLH and PAC values found are still returned

### Requirement: Cached with the record
The limits SHALL come from the same cached PUG View response as the properties and follow its cache time to live and request policy.

#### Scenario: Cache hit
- **WHEN** the record is in the cache
- **THEN** the limits are read from it with no request
