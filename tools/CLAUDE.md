# tools/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `tools/`.

- Tools must not import from `agent/`, and must not call an LLM.
- Tools must not import other tool subfolders; shared types go in `tools/schemas.py`.
- Never import a provider package (`langchain_openai`, ...) in `tools/`, with one exception:
  `tools/emissions/rag/embeddings.py` builds the default embeddings for the SCC retrieval
  (lazily, chosen by `[embeddings].provider`). Everything else takes `Embeddings` injected.
- Every tool uses `@tool`, has full type hints on inputs and outputs (TypedDicts,
  not bare `dict`), and a rich docstring: purpose, `Args:`, `Returns:` with units.
  The docstring is what the LLM sees, so keep it accurate.
- Helpers live in `<tool folder>/helpers/`, grouped in subfolders by what they do (for example
  `emissions/helpers/inventory/` and `stack/`, `exposure/helpers/meteorology/` and `population/`);
  a helper used by the whole folder stays at the `helpers/` root. Tests mirror this layout.
- New tools are added to the folder's `TOOLS` list and `tools/registry.py`, and
  to `tests/tools/test_registry.py` and add a test under the tool's folder in `tests/tools/`.
