# tools/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `tools/`.

- Tools must not import from `agent/`, and must not call an LLM.
- Tools must not import other tool subfolders; shared types go in `tools/schemas.py`.
- Never import a provider package (`langchain_openai`, ...) in `tools/`, with two exceptions:
  `tools/emissions/rag/embeddings.py` builds the default embeddings for the SCC retrieval
  (lazily, chosen by `[embeddings].provider`), and
  `tools/informatics/helpers/read_across/moldeberta.py` loads the MolDeBERTa SMILES encoder
  (lazily; the only module that imports `torch` or `transformers`). Everything else takes
  `Embeddings` or a `SmilesEmbedder` injected.
- A tool that calls a provider or service itself gets its key per call from `tools/credentials.py`
  (`PROVIDER_KEY`, `CENSUS_KEY`, `COMPTOX_KEY`, set by the web program or the CLI for one run)
  before its environment variable, and never stores the key on an object that outlives the call.
- Every tool uses `@tool`, has full type hints on inputs and outputs (TypedDicts,
  not bare `dict`), and a rich docstring: purpose, `Args:`, `Returns:` with units.
  The docstring is what the LLM sees, so keep it accurate.
- Helpers live in `<tool folder>/helpers/`, grouped in subfolders by what they do (for example
  `emissions/helpers/inventory/` and `stack/`, `exposure/helpers/meteorology/` and `population/`);
  a helper used by the whole folder stays at the `helpers/` root. Tests mirror this layout.
- New tools are added to the folder's `TOOLS` list and `tools/registry.py`, and
  to `tests/tools/test_registry.py` and add a test under the tool's folder in `tests/tools/`.
- A tool whose result is too large for the model returns `(content, artifact)` with `response_format="content_and_artifact"`: the model reads a ranked, capped `content` that says what was left out, and the program (the web workspace) reads the complete `artifact`. Never rely on the model to sort or filter a long list.
