## ADDED Requirements

### Requirement: Category membership before read-across
When the CAS number is not itself a TRI catalog chemical, the tool SHALL look it up in the
TRI category member list before contacting PubChem or computing an embedding. If it is a
member, the result SHALL report the category (code and name; all of them when there are
several), `is_direct_tri_match` false, resolution method "tri_category_member",
`within_applicability_domain` true, and a warning that says in plain words that the chemical
is not listed in TRI on its own but belongs to the named category, that releases are reported
under the category code for all its members together, and that no similarity is involved. The
similarity fields and the scaling factor SHALL be None. The chemical's own structure and
molecular weight SHALL be filled when they can be resolved, and a failure to resolve them
SHALL NOT turn the category match into an unresolved result. Only a chemical that is neither
a catalog chemical nor a category member SHALL go on to structural read-across.

#### Scenario: Member of one category
- **WHEN** the query is 95-57-8 and it is a member of N084 but not a catalog chemical
- **THEN** the result has resolution method "tri_category_member", category N084, no similarity scores, and a warning naming the category

#### Scenario: No network for the category step
- **WHEN** the query is a category member whose structure is not needed
- **THEN** the category is reported without an embedding computation

#### Scenario: Catalog chemical wins
- **WHEN** the CAS number is both a catalog chemical and a category member
- **THEN** the result is the direct match and carries no category

#### Scenario: Not a member either
- **WHEN** the CAS number is neither a catalog chemical nor a category member
- **THEN** structural read-across runs as before

#### Scenario: Structure cannot be resolved
- **WHEN** the query is a category member and PubChem is unavailable
- **THEN** the category is still reported, the structure fields are None, and a warning says why

## MODIFIED Requirements

### Requirement: Result shape
The tool SHALL return every field on every call: query CAS, query SMILES, query molecular
weight (g/mol), whether this is a direct TRI match, surrogate TRI CAS, name, SMILES and
molecular weight (g/mol), MolDeBERTa cosine similarity, ECFP4 Tanimoto similarity, hybrid
score, molecular-weight scaling factor (query MW / surrogate MW, dimensionless), whether
the match is within the applicability domain, the resolution method ("direct_tri_catalog_match",
"tri_category_member", "hybrid_read_across" or "unresolved"), the TRI categories found for the
query (a possibly empty list of code and name pairs), the TRI category the surrogate is
reported under (code and name, or None), and a warnings list. A value that could not be
obtained SHALL be None, and a warning SHALL say why.

#### Scenario: Value unavailable
- **WHEN** PubChem returns a SMILES but no molecular weight for the query
- **THEN** the surrogate is still selected, query MW and the scaling factor are None, and a warning says the molecular weight was not found

#### Scenario: Category fields on a plain read-across
- **WHEN** the query is neither a catalog chemical nor a category member
- **THEN** the query's category list is empty and the result has no category-member warning

#### Scenario: Surrogate that is a category member
- **WHEN** the chosen surrogate is a chemical TRI reports under category N100
- **THEN** the surrogate's category is N100 and its name

### Requirement: Description carries the decision guidance
The tool's description SHALL say first that it applies only to a chemical already identified by
a CAS number the user gave and never identifies a chemical from its name, and SHALL NOT read as
a sequence of other tools to call first. It SHALL say: use it when a chemical is not in TRI or
has no inhalation benchmark; a chemical that belongs to a TRI category is reported as a
category member and the user must be told it was matched through that category, not as itself
a listed chemical; report the hybrid score and the applicability-domain flag; a surrogate's
benchmark is a read-across estimate, not a measured value for the query chemical; and never
use a surrogate outside the applicability domain without saying so.

#### Scenario: Description audit
- **WHEN** the description audit runs over the registered tools
- **THEN** the read-across tool's description contains each pinned phrase, including the one about category members
