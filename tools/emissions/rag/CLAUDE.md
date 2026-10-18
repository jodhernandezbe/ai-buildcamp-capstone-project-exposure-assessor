# tools/emissions/rag/ rules

Project-wide guidance is in the root `CLAUDE.md` and `tools/CLAUDE.md`; these rules apply to
work in `tools/emissions/rag/`.

- SCC retrieval (RAG) for the emissions tools: read the SCC table, embed it, persist a
  vector index and run the LangGraph retrieval graph. No `@tool` definitions here (the tool
  is `tools/emissions/process.py`) and no chat or completion model calls: the agent's LLM
  reads what is retrieved.
- Module roles: `embeddings.py` provider factory, `vectorstore.py` Chroma index,
  `documents.py` SCC types and source reading, `graph.py` LangGraph graph, `retriever.py`
  public entry point (builds defaults at the outer edge), `errors.py` expected failures.
- Embeddings are injected as `langchain_core.embeddings.Embeddings`. Only `embeddings.py`
  may import a provider package (lazily, chosen by `[embeddings].provider`); a new provider
  is an entry there plus `config.retrieval.SUPPORTED_EMBEDDING_PROVIDERS`.
- Only `vectorstore.py` imports `chromadb`.
- Paths, columns, filters, model, top-k and batch size come from `[embeddings]` and
  `[scc_index]` in `config/settings.toml`; never hard-code them.
- The persisted index is a disposable cache under a gitignored directory; it rebuilds
  itself when the source table or its settings change.
- Provider and vector-store failures become `errors.py` exceptions inside this package and
  warnings at the retriever's edge; a provider exception never reaches the tool.
- Tests inject a fake `Embeddings` and a `tmp_path` index directory; never call a real
  provider outside `tests/smoke/`.
