## Why

Plume-rise and dispersion need stack height, diameter, exit velocity and exit temperature, but `fetch_stack_parameters_from_nei` is a stub and nothing covers facilities missing from the NEI. Separately, the agent only sees a NAICS description, so it cannot tell what physical process (and therefore which SCC and stack defaults) it is evaluating. This change gives stack parameters a tiered, fail-closed lookup and gives the agent plain-text process context.

## What Changes

- Rename the tier 1 tool to `fetch_stack_parameters_from_nei(frs_id)`; it stays a stub that raises `NotImplementedError`. Its implementation (and the `stack-parameters-nei` spec) moves to the follow-up change `add-nei-stack-parameters`.
- Add `fetch_stack_parameters_from_scc(scc_code)` (tier 2): look up SCC-keyed defaults in a bundled EPA PSTK (Point Source Stack Replacements) file in `data/`; if the SCC is absent, fall back to the AirToxScreen global point-source default (3.0 m, 0.2 m, 4.0 m/s, 295.4 K). The result states which level supplied the values. The tool description tells the LLM to call it only after tier 1 returned no usable values.
- Add `lookup_scc_process_description(naics_description)`: a LangGraph retrieval graph over a ChromaDB index of `data/epa_scc_to_epa_emission_sector.csv` (Point and Active SCCs only, about 9,000 rows). Given a NAICS description it returns the best-matching SCC codes with their level one to four text, so the LLM learns the physical process.
- Embeddings go through an injected `Embeddings` interface (LangChain); the default is OpenAI embeddings, built only at the outer edge so the provider can be swapped later.
- Add `[stack]`, `[scc_index]` settings (file paths, column names, units, fallback values, collection name, embedding model, top-k) to `config/settings.toml` with typed loaders.
- Make `StackParameters` values nullable and add `source`, `scc` and `warnings`.
- Add `chromadb` and `langchain-openai` dependencies (the provider package is imported only in `tools/emissions/rag/embeddings.py`).
- Repair the in-progress rename: `tools/emissions/__init__.py` and `tests/tools/emissions/test_stack.py` still reference `fetch_stack_parameters`.
- **BREAKING**: `fetch_stack_parameters` no longer exists; callers use the two tier functions.

## Capabilities

### New Capabilities
- `stack-parameters-scc-fallback`: tier 2 stack defaults by SCC from PSTK, with the AirToxScreen global default as the final fallback.
- `scc-process-context`: ChromaDB/LangGraph retrieval of SCC level one to four descriptions from a NAICS description.

### Modified Capabilities
- `app-configuration`: new `[stack]` and `[scc_index]` settings sections with typed loaders and validation.

## Impact

- Code: `tools/emissions/` (stack tiers, PSTK helpers, thin SCC tool) and `tools/emissions/rag/` (embeddings provider, vector store, SCC documents, LangGraph graph, retriever) with its own `CLAUDE.md`; `tools/schemas.py`; `config/` split into `parsing.py`, `stack.py`, `retrieval.py`; `CLAUDE.md` files (provider-import exception documented); tests mirroring each.
- Data: the user supplies a PSTK CSV in `data/`; the SCC CSV is already present (untracked).
- Dependencies: `chromadb`, `langchain-openai`; requires `OPENAI_API_KEY` at runtime for building and querying the index.
- Agent: three tools added to the bound tool list; the system prompt may need a line on tier ordering (left to the apply phase if it is not covered by tool descriptions).
