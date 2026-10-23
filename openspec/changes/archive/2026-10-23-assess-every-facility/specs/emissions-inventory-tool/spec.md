## MODIFIED Requirements

### Requirement: EIS IDs of many facilities, quickly
The same-site searches of facilities without their own EIS registration SHALL be made in bulk, one request for a configured number of facility names of one state (names the service cannot parse, such as those containing a comma, an ampersand or a slash, are not searched), matched locally by exact name, state and distance, and SHALL run a configured number of requests at a time, the EIS registrations of all the twins found SHALL be read together, and each facility's EIS IDs (or the reason it has none) SHALL be reused for a configured time within the process, so assessing hundreds of facilities stays practical and a repeated assessment makes no new EIS request.

#### Scenario: Repeated lookup
- **WHEN** the EIS IDs of the same facilities are asked for again within the reuse time
- **THEN** no request is made

#### Scenario: Twin registrations together
- **WHEN** several facilities need a same-site search
- **THEN** the registrations of every twin found are read in bulk, not one request per facility

#### Scenario: Same-site searches in bulk
- **WHEN** 100 facilities without their own registration need a same-site search and the batch size is 20
- **THEN** five requests are made, not one hundred, and each facility gets the same twin it would have got from its own request

#### Scenario: Names the service cannot parse
- **WHEN** a facility's site name contains a character the service's query parser rejects
- **THEN** no request is made for it (it would fail and be retried), and the facility keeps the existing note that no twin was found

#### Scenario: Rejected batch
- **WHEN** the service rejects a batch of names as an unparseable query
- **THEN** the batch is split and retried down to single names, and a name still rejected leaves that facility without a twin and with a note, never an exception
