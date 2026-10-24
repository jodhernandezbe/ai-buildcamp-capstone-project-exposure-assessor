## ADDED Requirements

### Requirement: Category facilities when TRI has no release of the chemical
When the CAS number has no TRI release of its own but is a member of one or more TRI categories,
the batch assessment SHALL take its facilities from those categories, asking the emissions
inventory for each category code with the same state and city filter. Facilities SHALL be one
per facility and medium; a facility reported under several categories SHALL keep its larger
release. The result SHALL say, in its warnings, that the chemical has no release of its own,
which categories its facilities are from, and that their releases cover every member of each
category together. The benchmarks SHALL remain the chemical's own. When the chemical has its own
TRI releases, those SHALL be used and the categories SHALL NOT be queried.

#### Scenario: Member with no own releases
- **WHEN** the CAS number is a member of category N084 and TRI has no release of it
- **THEN** the facilities are those reported under N084, and a warning names the category and says its releases cover every member

#### Scenario: Own releases win
- **WHEN** TRI has releases of the CAS number itself
- **THEN** only those are assessed and no category is queried

#### Scenario: Facility in two categories
- **WHEN** a facility reports under two categories of the chemical
- **THEN** it is assessed once, with the larger release, and a warning says so

#### Scenario: Benchmarks stay the chemical's own
- **WHEN** the chemical's facilities come from a category
- **THEN** the toxicity values are looked up for the chemical's CAS number

### Requirement: Analogue benchmarks are disclosed and gated
When the chemical has no inhalation benchmark of its own and none is given, the batch
assessment SHALL run the read-across tool. It SHALL use the nearest TRI analogue's benchmarks only
when that match is within the applicability domain, and SHALL then name the analogue, its name,
its hybrid score and the applicability-domain threshold in `toxicity_source`, and say in the
warnings that the values are a read-across estimate, not measured values for the chemical, and
that the molecular-weight scaling factor was not applied. An out-of-domain analogue SHALL NOT be
used; the warnings SHALL give its score and the threshold.

#### Scenario: In-domain analogue
- **WHEN** the chemical has no benchmark and its analogue scores at or above the threshold with a benchmark
- **THEN** the analogue's benchmark is used and `toxicity_source` names the analogue, its score and the threshold

#### Scenario: Out-of-domain analogue
- **WHEN** the analogue scores below the threshold
- **THEN** no benchmark is used and the warnings give the score and the threshold

#### Scenario: Own benchmark
- **WHEN** CompTox gives the chemical's own benchmark
- **THEN** no analogue is consulted

### Requirement: A failed TRI read is never a fallback trigger or an absence
When TRI cannot be read for the chemical or for a category, the batch assessment SHALL NOT use
the category route and SHALL NOT report that the chemical has no releases. It SHALL assess no
facility and report that the assessment was not completed because TRI could not be read, so the
user can retry. The emissions inventory tool SHALL report the same failure in its note, not an
empty list alone.

#### Scenario: Own read fails
- **WHEN** the TRI request for the chemical fails after its retries
- **THEN** no category is queried, no facility is assessed, and the warnings say the assessment was not completed

#### Scenario: Category read fails
- **WHEN** the TRI request for a category fails
- **THEN** the assessment is not completed and no partial set of facilities is assessed

#### Scenario: Emissions tool
- **WHEN** the emissions inventory tool cannot read TRI
- **THEN** the note says TRI could not be read and that this is not evidence of no releases
