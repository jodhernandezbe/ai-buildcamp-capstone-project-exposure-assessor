## Purpose

Pure, deterministic similarity equations for read-across. They score a query chemical
against every catalog chemical at once, using a learned embedding (cosine, corrected for the
embedding space's anisotropy) and a structural fingerprint (Tanimoto), combine the two into
one hybrid score, and pick the best candidate.

## ADDED Requirements

### Requirement: Isotropy correction by mean centering
Learned sentence-style embeddings occupy a narrow cone, so their raw cosines are compressed
into a high, poorly discriminating band. The system SHALL therefore provide a first-order
isotropy correction: given a reference mean vector mu, it SHALL subtract mu from a vector (or
from every row of a matrix) and L2-normalize the result, so the corrected vectors are unit
length and measured relative to the centre of the reference distribution. Centering and
normalizing SHALL happen in that order. The mean vector SHALL be computed as the arithmetic
mean of the reference matrix's rows. A width mismatch or a non-finite value SHALL raise
`ValueError`. A vector equal to mu has no direction once centred; the system SHALL report that
case rather than return a zero or arbitrary vector.

#### Scenario: Centering removes the shared component
- **WHEN** two vectors differ only in the component they share with mu
- **THEN** their centred, normalized forms are identical

#### Scenario: Still unit length
- **WHEN** a vector is centred and normalized
- **THEN** its L2 norm is 1.0

#### Scenario: Mean of the reference matrix
- **WHEN** the mean vector of a two-row matrix is computed
- **THEN** it is the element-wise average of those rows

#### Scenario: Vector at the centre
- **WHEN** a vector equals mu
- **THEN** the system reports that it has no direction instead of returning a vector

#### Scenario: Width mismatch
- **WHEN** mu has 768 entries and the vector has 512
- **THEN** a `ValueError` is raised

### Requirement: Vectorized cosine similarity
The system SHALL compute, for a query vector and a matrix of catalog vectors of the same
width, both already centred on the same mean vector and L2-normalized, one dimensionless
cosine similarity per catalog row as their dot product clipped to [-1, 1], in a single
vectorized operation. A width mismatch, an empty catalog or a non-finite value SHALL raise
`ValueError`.

#### Scenario: Identical vectors
- **WHEN** a catalog row equals the query vector
- **THEN** that row's cosine similarity is 1.0

#### Scenario: Orthogonal vectors
- **WHEN** a catalog row is orthogonal to the query vector
- **THEN** that row's cosine similarity is 0.0

#### Scenario: Rounding beyond one
- **WHEN** floating-point rounding makes a dot product slightly greater than 1
- **THEN** the returned similarity is exactly 1.0

#### Scenario: Width mismatch
- **WHEN** the query has 768 entries and the catalog rows have 512
- **THEN** a `ValueError` is raised

### Requirement: Vectorized Tanimoto similarity
The system SHALL compute, for a binary query fingerprint and a binary catalog fingerprint
matrix of the same width, one Tanimoto similarity per row as intersection / union, where
intersection is the count of bits set in both and union is the bits set in either. The
union SHALL be floored at 1e-9, so two all-zero fingerprints score 0.0 and never divide by
zero. Entries other than 0 and 1 SHALL raise `ValueError`.

#### Scenario: Identical fingerprints
- **WHEN** a catalog row has exactly the query's bits set
- **THEN** that row's Tanimoto similarity is 1.0

#### Scenario: Disjoint fingerprints
- **WHEN** a catalog row shares no set bit with the query
- **THEN** that row's Tanimoto similarity is 0.0

#### Scenario: Empty fingerprints
- **WHEN** both the query and a catalog row have no bits set
- **THEN** that row's similarity is 0.0 and no division error occurs

#### Scenario: Non-binary entry
- **WHEN** a fingerprint contains the value 2
- **THEN** a `ValueError` is raised

### Requirement: Hybrid read-across score
The system SHALL combine cosine and Tanimoto similarities as
alpha * cosine + (1 - alpha) * Tanimoto, with alpha in [0, 1] supplied by the caller. An
alpha outside [0, 1], or arrays of different length, SHALL raise `ValueError`.

#### Scenario: Weighted blend
- **WHEN** alpha is 0.55, cosine is 1.0 and Tanimoto is 0.0
- **THEN** the hybrid score is 0.55

#### Scenario: Invalid weight
- **WHEN** alpha is 1.2
- **THEN** a `ValueError` is raised

### Requirement: Best candidate selection
The system SHALL return the index of the highest hybrid score. Ties SHALL resolve to the
lowest index (the earliest catalog row).

#### Scenario: Tie
- **WHEN** rows 1 and 3 share the highest score
- **THEN** index 1 is returned

### Requirement: Leave-one-out score distribution
To let a threshold be calibrated against a catalog rather than guessed, the system SHALL
compute, for a reference catalog, each row's best hybrid score against every other row
(excluding the row itself). A catalog with fewer than two rows SHALL raise `ValueError`.

#### Scenario: Each row scored against the others
- **WHEN** the leave-one-out scores of a three-row catalog are computed
- **THEN** there are three scores and none is a row's score against itself

#### Scenario: Duplicate structures
- **WHEN** two catalog rows have the same embedding and fingerprint
- **THEN** both rows' leave-one-out scores are 1.0

#### Scenario: Too small to compare
- **WHEN** the catalog has one row
- **THEN** a `ValueError` is raised
