## ADDED Requirements

### Requirement: Community, occupational and profile results per facility
The system SHALL return for every fully assessed or worst-case-only facility its community result (the existing ambient result `exposure`, unchanged in name and value), its `occupational_exposure` and its `operational_profile`. Screening-out and tier selection SHALL remain driven by the community bound only: a facility is not screened out or kept because of its occupational result, and the occupational result SHALL be computed for every facility the assessment evaluates, including those kept at worst case only. The occupational fields SHALL appear in the program's complete result; the text the model reads SHALL carry each facility's tier and ratio in one line.

#### Scenario: Chemical looked up once
- **WHEN** the assessment is run
- **THEN** the limits and vapor pressure come from one lookup of the chemical, made with the values the user entered in the thread, also when the benchmarks were given

#### Scenario: Lookup cannot be made
- **WHEN** benchmarks are given and the lookup cannot be made
- **THEN** the assessment goes on, the worker result has no limit and the warnings say why

#### Scenario: Three results
- **WHEN** a facility is assessed
- **THEN** it carries community, occupational and profile results

#### Scenario: Screening unchanged
- **WHEN** a facility's community bound would screen it out
- **THEN** it is still screened out and the occupational result is not computed for it

#### Scenario: Worst-case-only facility
- **WHEN** a facility is kept at worst case only
- **THEN** its occupational result is still computed and its community result is the worst case

#### Scenario: One request
- **WHEN** many facilities are assessed
- **THEN** no request per facility is made for the occupational result beyond the single PubChem record of the chemical
