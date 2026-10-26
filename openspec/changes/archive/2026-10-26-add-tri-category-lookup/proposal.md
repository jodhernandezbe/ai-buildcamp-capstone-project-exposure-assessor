## Why

TRI reports many chemicals not under their own CAS number but under a **category** (for
example N420 "lead compounds" or N100 "copper compounds"). Today a chemical that is not a
discrete entry on the TRI list goes straight to structural read-across, even when TRI
already covers it through a category that names it. `data/chemicals_in_tri_categories.csv`
(2,693 rows, 92 category/type combinations) lists the member chemicals of each category, so
the agent can answer "is this chemical in TRI after all?" before it estimates by analogy.

## What Changes

- Resolution order for a chemical with a CAS number becomes: (1) discrete TRI chemical,
  (2) member of a TRI category, (3) structural read-across. Each step runs only if the
  previous one found nothing.
- A category member is reported with its category code and name, and the result always says
  that the chemical was matched through a category, never as a direct TRI match.
- The category's TRI code (for example N420) is the identifier used to look up reported
  releases, because TRI files category releases under the code, not under the member's CAS.
  Those releases cover the whole category and are disclosed as such.
- The organic category members become additional read-across candidates (the catalog
  builder adds them), so a chemical outside TRI can be matched to a category member that is
  structurally close.
- The system prompt and tool description teach the reasoning: say when a category stood in
  for a chemical, and what that does and does not tell the user.

## Capabilities

### New Capabilities
- `tri-category-membership`: loads the TRI category member list, validates it, and answers
  "which TRI category (if any) contains this CAS number".

### Modified Capabilities
- `tri-read-across-tool`: new resolution step and result fields for category membership;
  candidate set now includes category members.
- `tri-read-across-catalog`: builder adds organic category members as candidates, with their
  category codes.
- `emissions-inventory-tool`: accepts a category code as the lookup identifier and discloses
  that the releases are for the whole category.
- `agent-system-prompt`: states how a category match is reasoned about and disclosed.
- `facility-assessment-tool`: a chemical with no TRI release of its own is assessed on the
  facilities of its categories, with the category disclosed; its toxicity stays its own.

## Impact

- Code: `tools/informatics/read_across.py` and `helpers/read_across/`, a new category loader
  under `tools/informatics/helpers/`, `tools/emissions/helpers/inventory/tri.py`,
  `scripts/build_tri_embeddings.py`, `tools/schemas.py` (`ReadAcrossMatch`), `config/`
  (category file path and columns), `prompts/agent_system.md`.
- Data: `data/chemicals_in_tri_categories.csv` (already added); `data/tri_chemicals/*.parquet`
  rebuilt with new optional columns; `min_hybrid_score` recalibrated on the larger catalog.
- Evals: new scenario and cassette for a category-member chemical.
- No new dependencies and no new external services.
