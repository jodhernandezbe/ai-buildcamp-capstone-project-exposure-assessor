## ADDED Requirements

### Requirement: Inventory reused for a configured time
The inventory of a chemical for a place SHALL be reused, for the configured time, by later inventory calls and by the batch assessment within the same process, so TRI is read once; copies SHALL be returned, so a caller cannot change the remembered inventory.

#### Scenario: Listing then assessing
- **WHEN** the inventory is listed and the same chemical is then assessed within the reuse time
- **THEN** TRI is read once

#### Scenario: Reuse off
- **WHEN** the reuse time is 0
- **THEN** every call reads TRI

### Requirement: EIS IDs of many facilities, quickly
The same-site searches of facilities without their own EIS registration SHALL run a configured number at a time, the EIS registrations of all the twins found SHALL be read together, and each facility's EIS IDs (or the reason it has none) SHALL be reused for a configured time within the process, so assessing hundreds of facilities stays practical and a repeated assessment makes no new EIS request.

#### Scenario: Repeated lookup
- **WHEN** the EIS IDs of the same facilities are asked for again within the reuse time
- **THEN** no request is made

#### Scenario: Twin registrations together
- **WHEN** several facilities need a same-site search
- **THEN** the registrations of every twin found are read in bulk, not one request per facility
