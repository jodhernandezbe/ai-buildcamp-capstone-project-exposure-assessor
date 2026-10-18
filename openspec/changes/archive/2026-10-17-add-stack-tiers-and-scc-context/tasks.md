## 1. Prerequisites and repair

- [x] 1.1 Fix the in-progress rename: export `fetch_stack_parameters_from_nei` from `tools/emissions/__init__.py`, update `tests/tools/emissions/test_stack.py`, `tests/tools/test_registry.py` and the `query_emissions_inventory` docstring
- [x] 1.2 Add `chromadb` and `langchain-openai` with `uv add`; add `.cache/` to `.gitignore`

## 2. Configuration

- [x] 2.1 Move the shared validators from `config/loader.py` to public functions in `config/parsing.py` (add project-root path resolution); `loader.py` keeps its public API
- [x] 2.2 Add `[stack.pstk]`, `[stack.target_units]`, `[stack.ranges]`, `[stack.global_fallback]` to `settings.toml` and `config/stack.py` (`StackSettings`, `load_stack_settings`, `get_stack_settings`)
- [x] 2.3 Add `[embeddings]` and `[scc_index]` to `settings.toml` and `config/retrieval.py` (`EmbeddingSettings`, `SccIndexSettings`, loaders and cached getters)
- [x] 2.4 Tests in `tests/config/` for both modules, with one negative test per validation rule

## 3. Shared schema and units

- [x] 3.1 Make the `StackParameters` values nullable and add `source`, `scc`, `warnings`; add the `SccMatch` and `SccLookupResult` TypedDicts
- [x] 3.2 Add tests for absolute temperature conversion (32 degF -> 273.15 K, 72.05 degF -> 295.4 K) and ft -> m; update the offset-unit sentence in the `commons.units.convert` docstring

## 4. Tier 2 stack parameters

- [x] 4.1 `tools/emissions/helpers/stack_values.py`: pure parse -> convert -> range check of one row into four SI values or warnings; unit-convertibility check
- [x] 4.2 `tools/emissions/helpers/pstk.py`: cached PSTK reader (national rows, normalized SCC keys, duplicate count) and `scc_stack_parameters` resolution with global fallback
- [x] 4.3 `fetch_stack_parameters_from_scc(scc_code)` in `tools/emissions/stack.py`, with a docstring that says use only after NEI returned no values
- [x] 4.4 Tests with synthetic fixture CSVs for every `stack-parameters-scc-fallback` scenario plus the helpers' negative cases
- [x] 4.5 Make `scc_code` optional (null or omitted -> global default with a "no SCC given" warning, PSTK not read) in the helper and the tool, with tests
- [x] 4.6 SCC matching by exact digit string (no leading-zero stripping), integer SCC accepted, matched code returned, all-zero PSTK row not indexed, with tests

## 5. SCC retrieval (`tools/emissions/rag/`)

- [x] 5.1 Create `tools/emissions/rag/` with its `CLAUDE.md`; list it in the root `CLAUDE.md`; document the provider-import exception in `agent/CLAUDE.md` and `tools/CLAUDE.md`
- [x] 5.2 `errors.py` and `embeddings.py` (provider registry, guarded adapter, missing-key check)
- [x] 5.3 `vectorstore.py`: persistent Chroma with fingerprint/count rebuild, batched add, scored query
- [x] 5.4 `documents.py` (`SccDocument`, filter, dedupe, document text, fingerprint)
- [x] 5.5 `graph.py` (LangGraph validate -> ensure_index -> retrieve) and `retriever.py` (`SccRetriever`, `default_scc_retriever`)
- [x] 5.6 Tests in `tests/tools/emissions/rag/` with a keyword fake embedder and `tmp_path`: filter, dedupe, ranking, top-k bound, empty query makes no embed call, rebuild vs. reuse, half-built index, embedder error, missing key

## 6. SCC context tool

- [x] 6.1 `lookup_scc_process_description(naics_description)` in `tools/emissions/process.py`, mapping hits to `SccMatch` and failures to warnings
- [x] 6.2 Tests in `tests/tools/emissions/test_process.py` with an injected retriever
- [x] 6.3 `scripts/build_scc_index.py` to pre-build the index

## 7. Registration and verification

- [x] 7.1 Register the new tools in `TOOLS` and update `tests/tools/test_registry.py`
- [x] 7.2 Run ruff format, ruff check, pyright, bandit, the function-length check and pytest; all must pass
- [x] 7.3 `openspec validate add-stack-tiers-and-scc-context --strict`
