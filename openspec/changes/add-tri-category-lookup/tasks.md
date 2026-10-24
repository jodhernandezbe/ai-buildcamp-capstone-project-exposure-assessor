## 1. Category data and loader

- [x] 1.1 Add `[tri_categories]` to `config/settings.toml` (file path, column names, chemical-type values) with a typed loader module in `config/` and tests incl. missing column
- [x] 1.2 Implement the category index as `tools/tri_categories.py` (shared by tool folders) (read CSV, hyphenate digit-only codes, drop invalid CAS / empty codes with counts, lookup by CAS returning copies) with tests mirroring each scenario of `tri-category-membership`
- [x] 1.3 Test negative cases: bad check digit row, duplicate CAS in two categories, CAS not a member, file missing

## 2. Read-across tool

- [x] 2.1 Extend `ReadAcrossMatch` in `tools/schemas.py` with `query_categories` and `surrogate_category`; update `_unresolved`, `_direct` and the existing tests
- [x] 2.2 Add the category step between the catalog hit and the PubChem lookup, with best-effort structure fill and the disclosure warning; keep every function within 18 lines
- [x] 2.3 Update the tool description (category-member guidance and pinned phrase) and the description audit test
- [x] 2.4 Tests for each scenario in the modified `tri-read-across-tool` spec, with fakes (no network)

## 3. Emissions by category code

- [x] 3.1 Accept a category code in the emissions tool identifier check (valid CAS or known code), validate before any request
- [x] 3.2 Batch assessment: member CAS uses its categories' facilities when TRI has no own release; a read-across analogue supplies benchmarks only in domain, with disclosure of its name, score, threshold and category route
- [x] 3.3 Tests: category code, unknown code (no request), PCB CAS-style code via the CAS path

## 4. Catalog builder and recalibration

- [x] 4.1 Add organic category members to `scripts/build_tri_embeddings.py` helpers (skip inorganic and already-listed, merge category codes, reuse then resolve structures), with the report counts
- [x] 4.2 Add optional `catalog_source`, `category_codes` and `category_names` columns; loader tolerates old shards; tests for byte-identical rebuild and shard isolation
- [x] 4.3 (threshold kept at 0.60, see settings; all-rows recalibration pending user decision) Rebuild the catalog, recompute `min_hybrid_score` with `leave_one_out_scores` (all rows and TRI-list rows), update the settings comment, verify caffeine is out of domain and isohexane still maps to n-hexane

## 5. Prompt and evals

- [x] 5.1 Add the category-match reasoning to `prompts/agent_system.md` (no tool names) and its prompt test
- [x] 5.2 Eval scenario category-member-chlorophenol with its cassette; passes 3 of 3 runs (judge: category match disclosed)

## 6. Quality gates

- [x] 6.1 Run pytest, ruff format and check, pyright, bandit, function length, and the frontend check; fix findings
- [x] 6.2 Run `openspec validate add-tri-category-lookup --strict`
