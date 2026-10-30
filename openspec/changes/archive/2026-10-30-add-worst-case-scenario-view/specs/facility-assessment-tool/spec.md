## ADDED Requirements

### Requirement: Worst-case scenarios per assessed facility
The assessment SHALL return for every fully assessed facility its worst-case scenarios (one per registered pathway and quantity that has a value, today the community hazard quotient and cancer risk and the worker results) with the receptors of each, as defined by the worst-case scenario capability, and SHALL identify the driving facility of each. A scenario SHALL be built from the values the assessment already holds (the per-stack results, the facility's population tracts and the worker result) and SHALL NOT trigger another request. A worst-case-only facility SHALL carry the scenario its worst case supports, without receptors. The text the model reads SHALL name the driving facility and stack of each result in one line and SHALL NOT list the receptors.

#### Scenario: Full facility
- **WHEN** a facility is fully assessed
- **THEN** it carries its scenarios, each with the stack, conditions and ranked receptors

#### Scenario: Worst case only
- **WHEN** a facility is kept at worst case only
- **THEN** its scenario has the stack and conditions of the worst case and says receptors were not evaluated

#### Scenario: No extra requests
- **WHEN** the scenarios are built
- **THEN** no population or exposure request is made beyond the ones the assessment makes

#### Scenario: Driver in the text
- **WHEN** several facilities are assessed
- **THEN** the text the model reads names which facility and stack drive each result
