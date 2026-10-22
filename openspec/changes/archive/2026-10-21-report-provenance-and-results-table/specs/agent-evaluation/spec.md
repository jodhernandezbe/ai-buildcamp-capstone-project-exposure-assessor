## ADDED Requirements

### Requirement: The report names each input's source
A scenario MAY declare a deterministic check that the final report names the source of each input the run obtained: for every weather, residents and properties result in the record, the distinctive part of its `source` text (for example "era5", "ACS", "CompTox", a benchmark source name) SHALL appear in the report, and the chemical SHALL be referred to by the name the properties result gave or by its CAS number, never by another name. The expected strings SHALL come from the record's tool outputs.

#### Scenario: Weather source paraphrased
- **WHEN** the weather result's source is "Open-Meteo era5 reanalysis 2024" and the report says only "local weather"
- **THEN** the check fails and names the missing source

#### Scenario: Invented chemical name
- **WHEN** the properties result has no name and the report calls the chemical by a name
- **THEN** the check fails
