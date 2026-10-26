## ADDED Requirements

### Requirement: Organic category members are read-across candidates
The builder SHALL add to the catalog the organic members of the TRI category list that have a
valid CAS number and a parseable structure, so that a query chemical can be matched to a
category member. Inorganic members SHALL NOT be added, because the structure encoder and
fingerprint are not meaningful for metals and salts. A member whose CAS number is already a
discrete TRI chemical SHALL appear once, as the discrete chemical. A member listed under
several categories SHALL appear once and carry all its category codes. Each added row SHALL
be marked as coming from a category and carry its category codes and names, and rows from the
TRI list SHALL carry none. Structures SHALL be reused from the existing catalog, then resolved
on PubChem, exactly as for TRI-listed chemicals; a member with no parseable structure SHALL be
left out and listed in the report with the number added, skipped as inorganic, skipped as
already listed, and left out for lack of a structure.

#### Scenario: Organic member added
- **WHEN** an organic category member with a parseable structure is not a TRI-listed chemical
- **THEN** it is in the catalog, marked as from a category, with its category code

#### Scenario: Inorganic member skipped
- **WHEN** a category member is typed inorganic
- **THEN** it is not in the catalog and is counted as skipped

#### Scenario: Already a TRI chemical
- **WHEN** a category member's CAS number is also a discrete TRI chemical
- **THEN** the catalog has one row for it, marked as from the TRI list

#### Scenario: Several categories
- **WHEN** an organic member is listed under two categories
- **THEN** one row carries both category codes

#### Scenario: Byte-identical rebuild
- **WHEN** the catalog is rebuilt twice with no change to the inputs
- **THEN** every shard is byte-identical between the two runs

### Requirement: Applicability threshold is recalibrated when candidates change
The configured minimum hybrid score SHALL be recalibrated against the leave-one-out
nearest-neighbour score distribution of the catalog that includes the category members, and
the new calibration (catalog size, percentile used, resulting in-domain share) SHALL be
recorded beside the value. The distribution SHALL also be reported separately for the
TRI-listed rows alone, so the effect of the added candidates is visible.

#### Scenario: Calibration recorded
- **WHEN** the category members have been added
- **THEN** the configuration comment records the catalog size, the percentile and the in-domain share for the new catalog

#### Scenario: Caffeine still outside the domain
- **WHEN** caffeine (58-08-2) is scored against the new catalog
- **THEN** it is outside the applicability domain
