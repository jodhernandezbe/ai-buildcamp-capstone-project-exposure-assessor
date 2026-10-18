"""Build (or reuse) the persisted SCC vector index, then run one sample lookup.

The SCC tool builds the index on first use anyway; run this beforehand so the agent's first
call is fast. It needs the embedding provider's API key (``[embeddings].api_key_env_var``,
e.g. in ``.env``) and calls the provider once per ``[scc_index].batch_size`` documents.

Usage: ``uv run python scripts/build_scc_index.py ["industry description"]``
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from dotenv import load_dotenv

from tools.emissions.rag.errors import EmbeddingError
from tools.emissions.rag.retriever import default_scc_retriever

DEFAULT_QUERY = "Petroleum Refineries"


def main(argv: Sequence[str]) -> int:
    """Build the index and print the matches for ``argv[0]`` (or ``DEFAULT_QUERY``)."""
    load_dotenv()
    query = argv[0] if argv else DEFAULT_QUERY
    try:
        retriever = default_scc_retriever()
    except EmbeddingError as exc:
        print(f"cannot build the SCC index: {exc}", file=sys.stderr)
        return 1
    lookup = retriever.lookup(query)
    for warning in lookup.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for hit in lookup.hits:
        document = hit.document
        print(f"{hit.score:.3f}  {document.scc}  {document.level_three} > {document.level_four}")
    return 0 if lookup.hits else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
