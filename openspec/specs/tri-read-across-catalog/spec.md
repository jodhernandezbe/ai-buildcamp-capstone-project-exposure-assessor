# tri-read-across-catalog Specification

## Purpose

An offline builder that turns EPA's current TRI chemical list (Envirofacts `tri_chem_info`)
into the committed read-across catalog. For each discrete, currently listed TRI chemical,
the catalog holds the identity, canonical structure, molecular weight, embedding and
fingerprint. Rerunning it keeps the catalog in step with the TRI list.

## Requirements

### Requirement: Read the TRI chemical list from Envirofacts
The builder SHALL read the TRI chemical list from the configured Envirofacts
`tri_chem_info` path, using the shared Envirofacts base URL and request policy, and take
each chemical's CAS number, name and inactive date from the configured fields. It SHALL
request further pages while a page comes back full. If the list cannot be read (request
failure, malformed body, or a configured field missing), the builder SHALL exit with an
error and SHALL NOT overwrite the existing catalog. The output path SHALL be overridable on
the command line, with the default from configuration.

#### Scenario: Single page
- **WHEN** the first page returns fewer rows than the page size
- **THEN** no further page is requested

#### Scenario: Full page
- **WHEN** the first page returns exactly the page size
- **THEN** the next page is requested and its rows are added

#### Scenario: Envirofacts unavailable
- **WHEN** the list request times out after its retries
- **THEN** the builder exits non-zero, names the failure, and the existing catalog file is unchanged

### Requirement: Keep only discrete, listed chemicals
The builder SHALL drop rows whose CAS field is not a valid CAS registry number. These are
TRI groups and placeholders, such as N420 (lead compounds), MIXTURE, TRD SECRT and NA. It
SHALL also drop chemicals delisted from TRI (an inactive date other than the configured
"still active" value), unless configuration says to keep them. It SHALL keep only the first
row of a duplicated CAS number, and SHALL report how many rows were dropped and why.

#### Scenario: Group code
- **WHEN** a row's CAS field is "N420"
- **THEN** it is not in the catalog and is counted as a dropped group

#### Scenario: Delisted chemical
- **WHEN** a row's inactive date is 1994
- **THEN** it is not in the catalog and is counted as delisted

#### Scenario: Duplicate CAS
- **WHEN** two rows share CAS 50-00-0
- **THEN** the catalog has one 50-00-0 row

### Requirement: Reuse on-disk structures, resolve new chemicals on PubChem
For each kept chemical, the builder SHALL reuse the canonical SMILES and molecular weight
stored for that CAS number in the existing catalog file, when one exists. Only chemicals
missing from it SHALL be looked up on PubChem, with polite throttling and retry with
backoff, and their SMILES canonicalized and molecular weight computed from the structure, in
g/mol. Chemicals that still have no parseable structure SHALL be dropped and listed in the
report.

#### Scenario: Chemical already on disk
- **WHEN** 71-43-2 is in the existing catalog and in the TRI list
- **THEN** its stored SMILES is reused and no PubChem request is made for it

#### Scenario: Newly listed chemical
- **WHEN** a CAS number is in the TRI list but not in the existing catalog
- **THEN** its SMILES comes from PubChem and it appears in the new catalog

#### Scenario: First build
- **WHEN** no catalog file exists yet
- **THEN** every kept chemical is resolved on PubChem

#### Scenario: Unresolvable chemical
- **WHEN** PubChem has no parseable structure for a CAS number
- **THEN** the chemical is dropped and listed in the report

#### Scenario: Chemical no longer listed
- **WHEN** a CAS number is in the existing catalog but no longer in the TRI list
- **THEN** it is not in the new catalog

### Requirement: Catalog schema
The builder SHALL write the catalog as parquet shards, one file per leading CAS digit and
each sorted by CAS number, with one row per kept chemical and these columns:
`tri_cas`, `chemical_name`, `canonical_smiles`, `molecular_weight` (g/mol), `moldeberta_vec`
(768 floats, L2-normalized as the model produces them, not centred) and `morgan_bits` (1024
integers in {0, 1}, ECFP4 radius 2). The isotropy correction SHALL NOT be baked into the
stored vectors: the mean embedding is derived from them when the catalog is loaded, so the
correction can change without rebuilding the catalog. Embeddings and fingerprints SHALL be
recomputed for every row on each build. The widths SHALL come from configuration and match
what the tool expects.

#### Scenario: Round trip
- **WHEN** the tool loads a catalog the builder wrote
- **THEN** it accepts every row with no schema error

#### Scenario: Stored vectors are uncentered
- **WHEN** a catalog row's stored embedding is read
- **THEN** it is the model's own L2-normalized output for that SMILES, unchanged

### Requirement: Sharded, compact, reproducible storage
The builder SHALL split the catalog into one file per leading CAS digit (the number of digits
from configuration), so that no committed file exceeds the repository's file-size limit. It
SHALL store embeddings as 32-bit floats and fingerprint bits as 8-bit integers, compressed.
The same inputs SHALL always produce byte-identical shards: a chemical's stored molecular
weight SHALL NOT depend on how its SMILES was spelled. The builder SHALL stage every shard and
replace the existing ones only when all are written, and SHALL remove a shard whose digit no
longer has any chemical.

#### Scenario: Shard per leading digit
- **WHEN** the catalog holds 110-54-3 and 71-43-2
- **THEN** two shards are written, one named for digit 1 and one for digit 7

#### Scenario: Compact types
- **WHEN** a shard is read back
- **THEN** its embeddings are 32-bit floats and its fingerprint bits are 8-bit integers

#### Scenario: A rebuild changes only what changed
- **WHEN** a chemical is added to the TRI list and the catalog is rebuilt
- **THEN** only the shard for that chemical's digit differs; every other shard is byte-identical

#### Scenario: Back-to-back rebuilds
- **WHEN** the catalog is rebuilt twice with no change to the TRI list
- **THEN** every shard is byte-identical between the two runs

#### Scenario: A failed build leaves the catalog alone
- **WHEN** the build fails before all shards are staged
- **THEN** the existing shards are unchanged and no temporary file remains

#### Scenario: Spelling does not change the weight
- **WHEN** the same molecule is given as two different SMILES strings
- **THEN** its stored molecular weight is identical

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
