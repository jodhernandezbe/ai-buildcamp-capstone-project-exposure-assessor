## Purpose

Gives the agent one tool that maps a CAS number to its closest TRI chemical, as a direct
catalog match or as a read-across surrogate. The tool reports how similar the two are,
whether the match falls inside the applicability domain, and the molecular-weight ratio
needed to adjust a surrogate's benchmark. It never invents a value.

## ADDED Requirements

### Requirement: Validate the query CAS number
The tool SHALL strip whitespace from the CAS number and validate it, including the check
digit, before any lookup. An invalid CAS number SHALL return a result with every
similarity, surrogate and molecular-weight field None, `within_applicability_domain` false,
and a warning saying the CAS number is invalid, and SHALL make no network request.

#### Scenario: Surrounding whitespace
- **WHEN** the input is " 110-54-3 "
- **THEN** it is treated as 110-54-3

#### Scenario: Bad check digit
- **WHEN** the input is "110-54-4"
- **THEN** the result carries no surrogate, a warning says the CAS number is invalid, and no HTTP request is made

### Requirement: Result shape
The tool SHALL return every field on every call: query CAS, query SMILES, query molecular
weight (g/mol), whether this is a direct TRI match, surrogate TRI CAS, name, SMILES and
molecular weight (g/mol), MolDeBERTa cosine similarity, ECFP4 Tanimoto similarity, hybrid
score, molecular-weight scaling factor (query MW / surrogate MW, dimensionless), whether
the match is within the applicability domain, the resolution method, and a warnings list.
A value that could not be obtained SHALL be None, and a warning SHALL say why.

#### Scenario: Value unavailable
- **WHEN** PubChem returns a SMILES but no molecular weight for the query
- **THEN** the surrogate is still selected, query MW and the scaling factor are None, and a warning says the molecular weight was not found

### Requirement: Optional candidate filters
The tool SHALL accept `require_toxicity_benchmarks` (default false) and
`sector_naics_prefix` (default none). When `require_toxicity_benchmarks` is true and the
catalog has a benchmark flag column, only flagged chemicals SHALL be candidates. When a
NAICS prefix is given and the catalog has a NAICS-prefix column, only chemicals listed
under that prefix SHALL be candidates; if that leaves no rows, the unfiltered candidates
SHALL be used. When a requested filter's column is absent, or a filter falls back, the tool
SHALL add a warning saying so.

#### Scenario: Benchmark filter
- **WHEN** `require_toxicity_benchmarks` is true and the catalog flags only benzene
- **THEN** benzene is the only candidate

#### Scenario: Missing filter column
- **WHEN** `require_toxicity_benchmarks` is true and the catalog has no benchmark flag column
- **THEN** all catalog chemicals are candidates and a warning says the filter could not be applied

#### Scenario: Empty sector filter
- **WHEN** a NAICS prefix matches no catalog chemical
- **THEN** the unfiltered candidates are used and a warning says so

### Requirement: Direct TRI match fast path
The tool SHALL return immediately when the CAS number is among the candidates, without
contacting PubChem or computing an embedding. The result SHALL carry the catalog row as the
surrogate, all three similarities and the scaling factor equal to 1.0,
`is_direct_tri_match` true, `within_applicability_domain` true and resolution method
"direct_tri_catalog_match".

#### Scenario: n-Hexane is in the catalog
- **WHEN** the query is 110-54-3 and the catalog contains n-hexane
- **THEN** the result is a direct match for 110-54-3 with scores of 1.0 and no HTTP request is made

### Requirement: Resolve the query structure from PubChem
When the CAS number is not a candidate, the tool SHALL look up its SMILES and molecular
weight on PubChem PUG REST by name. The SMILES SHALL be read from the first present of the
canonical, isomeric and connectivity SMILES properties and canonicalized before use. The
request SHALL be time-bounded and retried per configuration. A failed request, unknown
compound, malformed body or unparseable SMILES SHALL yield no surrogate and a warning; the
tool SHALL NOT raise, and the result SHALL NOT be cached.

#### Scenario: Property alias
- **WHEN** PubChem returns only `ConnectivitySMILES`
- **THEN** that SMILES is used

#### Scenario: PubChem unavailable
- **WHEN** the PubChem request times out after its retries
- **THEN** the result has no surrogate, `within_applicability_domain` false, and a warning says the structure could not be resolved

#### Scenario: Unparseable SMILES
- **WHEN** PubChem returns a SMILES that cannot be parsed
- **THEN** the result has no surrogate and a warning names the SMILES problem

### Requirement: Select the closest surrogate
For a resolved query, the tool SHALL compute its embedding and ECFP4 fingerprint, score
every candidate with the hybrid read-across score using the configured alpha, and return
the highest-scoring candidate with its three similarities. The resolution method SHALL be
"hybrid_read_across".

#### Scenario: Isohexane to n-hexane
- **WHEN** the query is 107-83-5 (2-methylpentane, CCCC(C)C, 86.18 g/mol) and the candidates are n-hexane, benzene and trichloroethylene, with embeddings that make n-hexane the closest
- **THEN** the surrogate is 110-54-3, `is_direct_tri_match` is false and the scaling factor is 1.0

#### Scenario: Isohexane against the real catalog
- **WHEN** 107-83-5 is scored against the committed TRI catalog with the real embedding model
- **THEN** the surrogate is 110-54-3 (n-hexane), not an oxygenated chemical of similar size

### Requirement: Embeddings are compared in the catalog's centred space
The tool SHALL correct the embedding space's anisotropy before any cosine is taken: it SHALL
derive one mean embedding vector from the whole catalog, hold it with the catalog, and centre
and L2-normalize both the catalog embeddings and the query embedding on that same mean vector.
The mean vector SHALL come from the full catalog, never from a filtered subset, so a filter
narrows which chemicals can be chosen but never changes a pair's cosine. A query whose
embedding equals the mean vector SHALL yield no surrogate and a warning, not an error.

#### Scenario: Filters do not move the scores
- **WHEN** one query is scored against all candidates, and again with a filter that keeps the
  chosen surrogate
- **THEN** the reported cosine, Tanimoto and hybrid score are the same in both calls

#### Scenario: Identical structure still scores one
- **WHEN** a query's embedding equals a candidate's embedding
- **THEN** that candidate's cosine similarity is 1.0

#### Scenario: Query at the centre of the catalog
- **WHEN** a query's embedding equals the catalog's mean embedding
- **THEN** the result has no surrogate and a warning says the embedding carries no direction

### Requirement: Applicability domain
The tool SHALL set `within_applicability_domain` true only when the best hybrid score is at
least the configured threshold. The threshold SHALL be calibrated against the catalog's
leave-one-out nearest-neighbour score distribution, not guessed, and the calibration SHALL be
recorded with the value. When the flag is false, a warning SHALL say the surrogate is outside
the applicability domain and must not be used for read-across without expert justification.
Because a centred cosine is measured relative to the catalog's mean embedding, a score is
comparable only within one catalog version, and the tool SHALL NOT present scores from
different catalog versions as equivalent.

#### Scenario: Unrelated molecule
- **WHEN** the best hybrid score is 0.31 and the threshold is 0.60
- **THEN** `within_applicability_domain` is false, the best candidate is still reported, and the warning is present

#### Scenario: At the threshold
- **WHEN** the best hybrid score equals the threshold
- **THEN** `within_applicability_domain` is true

#### Scenario: A chemical unlike anything on the TRI list
- **WHEN** caffeine (58-08-2) is scored against the committed TRI catalog with the real embedding model
- **THEN** its best score is below the threshold, `within_applicability_domain` is false and the warning is present

#### Scenario: Threshold rejects a usable share of the catalog
- **WHEN** the threshold is applied to the catalog's own leave-one-out scores
- **THEN** it rejects a documented, non-trivial share of them, so the domain check discriminates rather than admitting nearly everything

### Requirement: Molecular-weight scaling factor
The tool SHALL report query MW / surrogate MW as `mw_scaling_factor` and SHALL NOT apply it
to any toxicity value. It SHALL be None when either molecular weight is missing,
non-finite or not positive.

#### Scenario: Equal weights
- **WHEN** both molecular weights are 86.18 g/mol
- **THEN** the factor is 1.0

### Requirement: Catalog availability
The tool SHALL read every shard of the catalog from its configured directory once per
process, treat them as one catalog and reuse it. A missing or malformed catalog (no shard,
shards with different columns, missing required columns, vectors of the wrong width, or fewer
than two chemicals) SHALL raise an error naming the location or column, because that is a
setup error, not a data problem.

#### Scenario: Catalog missing
- **WHEN** the configured catalog directory holds no shard
- **THEN** an error naming the directory and the build command is raised

#### Scenario: Shards read as one catalog
- **WHEN** the catalog is split across several shards
- **THEN** a query is scored against the chemicals of all of them

#### Scenario: Shards disagree
- **WHEN** one shard lacks a column another has
- **THEN** an error names the offending shard

### Requirement: Description carries the decision guidance
The tool's description SHALL say first that it applies only to a chemical already identified by
a CAS number the user gave and never identifies a chemical from its name, and SHALL NOT read as
a sequence of other tools to call first. It SHALL say: use it when a chemical is not in TRI or
has no inhalation benchmark; report the hybrid score and the applicability-domain flag; a surrogate's
benchmark is a read-across estimate, not a measured value for the query chemical; and never
use a surrogate outside the applicability domain without saying so.

#### Scenario: Description audit
- **WHEN** the description audit runs over the registered tools
- **THEN** the read-across tool's description contains each pinned phrase
