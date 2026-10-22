## MODIFIED Requirements

### Requirement: Facilities
The state SHALL list one facility per FRS ID from the emissions inventory results (latest
result wins; the complete list the tool returns beside the text the model reads, falling back to the
facilities in that text), with name, address fields, coordinates, TRI document control number, reported
release and its unit, emission rate (g/s), assumed operating hours (h/yr), medium, reporting
year, the TSCA conditions of use and life cycle stages the inventory reported for it (with the
note when there are none), and the queried CAS number. It SHALL attach, by matching identifiers only:
- industry (NAICS code, title, origin) from the industry tool, matched by document control number;
- stack candidates and their source from the NEI stack tool, matched by FRS ID;
- receptors (population, age distribution, radius used, source) from the population tool,
  matched by coordinates equal to the facility's within a configured tolerance;
- exposure results (per-stack results and ranges) from the exposure tool, matched by an
  emission rate equal to exactly one facility's emission rate.
A result that matches no facility, or more than one, SHALL NOT be attached to any facility and
SHALL be reported as an unattributed result.

#### Scenario: Stacks attached
- **WHEN** the NEI stack tool is called with a facility's FRS ID
- **THEN** that facility shows its candidates with source NEI

#### Scenario: Ambiguous exposure result
- **WHEN** two facilities share the emission rate passed to the exposure tool
- **THEN** the exposure result is attached to neither and is listed as unattributed

#### Scenario: Conditions of use carried
- **WHEN** the inventory record has two conditions of use and two life cycle stages
- **THEN** the facility shows both, unchanged, and no condition is derived by the workspace

#### Scenario: Older state without conditions
- **WHEN** a record has no conditions fields
- **THEN** the facility has empty lists and no note, and the state still builds
