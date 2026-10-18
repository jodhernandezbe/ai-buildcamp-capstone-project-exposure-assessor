## Context

- `tools/emissions/stack.py` holds an uncommitted rename to `fetch_stack_parameters_from_nei(frs_id)`, still a stub. `tools/emissions/__init__.py`, `tests/tools/emissions/test_stack.py`, `tests/tools/test_registry.py` and the `query_emissions_inventory` docstring still name `fetch_stack_parameters`.
- `StackParameters` (`tools/schemas.py`) has non-optional floats and no provenance.
- `commons/units.convert` wraps Pint with config aliases. `config/loader.py` (about 520 lines) keeps one frozen dataclass per section with `load_*`/cached `get_*` pairs, and private parse helpers.
- `data/epa_scc_to_epa_emission_sector.csv`: 14,138 rows, 27 columns, **no NAICS column**; 9,490 Point rows; level four is always filled. NAICS-to-SCC is therefore a semantic match on SCC text.
- Layer rules: tools must not call an LLM or import a provider package (`langchain_openai`, ...); `commons` and `config` import nothing from the project; functions are at most 18 body lines; paths, units and model names belong in `config/`.

## Goals / Non-Goals

**Goals:**
- Tier 2 stack lookup (PSTK, then global fallback) reading local files only.
- SCC retrieval (RAG) inside the emissions tool group (`tools/emissions/rag/`) with a swappable embeddings provider.
- Every value a user may want to tune (paths, columns, units, ranges, fallbacks, model, top-k, batch size) lives in `settings.toml`.
- No network or OpenAI calls in unit tests.

**Non-Goals:**
- **Tier 1 NEI implementation moved to the follow-up change `add-nei-stack-parameters`** (with its `stack-parameters-nei` spec). In this change the NEI tool is only renamed, with its docstring kept accurate, and it still raises `NotImplementedError`.
- Downloading PSTK data, NAICS-code crosswalks, county-specific PSTK overrides.
- A generation or rerank step in the retriever: the main agent's LLM reads the retrieved text.
- Changes to the agent graph or system prompt.

## Decisions

**D1. Two tools, not one tool that chains internally.** Tier 1 takes `frs_id` and tier 2 takes `scc_code`. Those inputs come from different upstream steps, and a combined tool would invite guessed SCCs. Both return `StackParameters` with a `source` field.

**D2. `StackParameters` becomes nullable with provenance:** the four values are `float | None`, plus `source: Literal["NEI", "PSTK", "AirToxScreen global default"] | None`, `scc: str | None` and `warnings: list[str]`.

**D3. Config split by concern.** Shared validators move from `config/loader.py` into `config/parsing.py` as public functions; `loader.py` keeps its public API and imports them. New modules:
- `config/stack.py` holds `StackSettings` for `[stack.pstk]` (path, SCC column, optional FIPS column plus national FIPS values, per-quantity columns and source units), `[stack.target_units]`, `[stack.ranges]` and `[stack.global_fallback]`.
- `config/retrieval.py` holds `EmbeddingSettings` for `[embeddings]` (provider, model, API-key env var, timeout) and `SccIndexSettings` for `[scc_index]` (source path, persist dir, collection, categories, statuses, column mapping, top_k, batch size).

Relative paths resolve against the project root. Alternative: keep appending to `loader.py`. Rejected because the file mixes four services already.

**D4. Unit convertibility is checked at first use, not in `config/`.** `config` may not import `commons`. When the PSTK helper first loads a file, it test-converts each source unit to the target unit and raises `ValueError` (a setup error) if one cannot be converted.

**D5. PSTK reading with stdlib `csv`, cached once per path.** Only national rows are kept: FIPS empty, or one of the configured national values. With no FIPS column configured, every row counts as national. Keys are SCCs as digit strings with surrounding whitespace removed and nothing else changed: SCCs have a fixed length, so a code with an extra leading zero is another code and does not match. The file's all-zero row is its own global default, not an SCC, and is not indexed. The tool also accepts an integer SCC (some LLMs emit all-digit codes as numbers) and returns the matched code, not the raw input. The first national row per SCC wins, and duplicates are counted in a warning. A missing or unreadable file is a data problem: the tool falls back to the global default with a warning.

**D6. Row validation is a pure pipeline:** parse each value (reject `bool`, non-finite and non-positive values), convert with `commons.units.convert` (Pint handles degF → K as an absolute temperature), then check the configured SI range. A row yields all four values or none.

**D7. The RAG lives in `tools/emissions/rag/`**, since it serves only the emissions tools (user decision; an earlier draft had a top-level `rag/` layer). It has its own `CLAUDE.md`. It never imports `agent` or `prompts` and never calls a chat model. Modules:
- `embeddings.py`: `build_embeddings(EmbeddingSettings) -> Embeddings`, with a provider registry (`{"openai": ...}`). It is the **only** module in `tools/` that imports a provider package (lazily). This is a documented exception to the no-provider-imports rule in `agent/CLAUDE.md` and `tools/CLAUDE.md`. `GuardedEmbeddings` turns provider and HTTP errors into `EmbeddingError` and validates the vectors. A missing API key raises `EmbeddingError` naming the variable.
- `vectorstore.py`: the only `chromadb` importer. It opens a `PersistentClient` with telemetry off and uses cosine space. It rebuilds when the fingerprint or the expected count in the collection metadata differs, so a half-built index is never reused. It adds documents in batches and returns scored hits with their metadata.
- `documents.py`: frozen `SccDocument`; reads the SCC CSV, filters by category and status, drops rows without SCC or level four, dedupes, and computes the fingerprint (sha256 of the file plus the indexing and embedding settings).
- `graph.py`: LangGraph `StateGraph` `validate → ensure_index → retrieve`. An empty query or a failed index step routes to `END`. Nodes turn the expected errors into warnings.
- `retriever.py`: `SccRetriever` (the compiled graph, with `lookup(text) -> SccLookup`) and `default_scc_retriever()`, the outer edge where settings and the default embeddings are built.

**D8. Chroma used directly (`chromadb`), not `langchain-chroma`.** This gives direct control of collection metadata for the fingerprint. Passing our own embeddings avoids Chroma's default ONNX embedder download. Score = `max(0, 1 − cosine distance)`.

**D9. The tool `lookup_scc_process_description` lives in `tools/emissions/process.py`.** It calls the default retriever and maps `SccHit` to the `SccMatch` TypedDict. If retriever construction fails (missing key), it returns an empty result with a warning. The retriever is cached only after it is built successfully.

## Risks / Trade-offs

- [The PSTK file is not in the repo yet] → Columns and units are config-driven, and tier 2 still answers with the global default. Tests use synthetic fixtures with clearly fake codes.
- [First SCC query builds the index: about 9k embeddings, an OpenAI cost and some seconds] → Built once and persisted under a gitignored `.cache/`; rebuilt only on fingerprint change.
- [Semantic matches can be plausible but wrong] → Return top-k with scores and all four levels. The tool description calls them candidates.
- [`commons.units.convert` docstring says offset units are not intended] → Add tests for absolute degF → K and update that sentence.
- [chromadb typing under strict pyright] → Keep chromadb calls inside `tools/emissions/rag/vectorstore.py`; pass NumPy arrays where its stubs need them.

## Migration Plan

1. Fix the rename so the suite imports again.
2. Config split, then schema, then tier 2, then the SCC RAG and its tool.
3. Rollback: revert the commit. The index is a disposable cache.
