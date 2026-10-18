"""LangGraph retrieval graph for SCC process descriptions.

    START -> validate --(empty or code-only query)--> END
                 \\-> ensure_index --(index unavailable)--> END
                          \\-> retrieve -> END

There is no generation node: the graph only retrieves, and the agent's LLM reads the result.
"""

from __future__ import annotations

import operator
import re
from collections.abc import Callable, Sequence
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from tools.emissions.rag.documents import SccDocument, SccHit
from tools.emissions.rag.errors import RetrievalError
from tools.emissions.rag.vectorstore import IndexedDocument, ScoredDocument, VectorIndex


class SccState(TypedDict):
    """Graph state: the query, what was found, and why anything is missing."""

    query: str
    hits: list[SccHit]
    warnings: Annotated[list[str], operator.add]
    failed: bool


class SccUpdate(TypedDict, total=False):
    """Partial state returned by a node."""

    query: str
    hits: list[SccHit]
    warnings: list[str]
    failed: bool


SccGraph = CompiledStateGraph[SccState, None, SccState, SccState]


_CODE_WORDS = frozenset({"naics", "code", "number", "no"})
_NUMERIC = r"[\W_]*\d[\d\W_]*"
_CODE_ONLY = (
    "the industry description is only a NAICS code ({given!r}); a code means nothing to a text "
    "search, so give the industry's name in words (the NAICS title, for example "
    "'Petroleum Refineries')"
)


def industry_text(query: str) -> str:
    """Return the words of an industry description, without any NAICS code or its label.

    Numeric tokens (``324110``, ``324-110``), stray punctuation and, next to a number, the
    label words "NAICS" and "code" are dropped because the index holds process descriptions,
    not codes: they only add noise to the similarity search. The result is empty when nothing
    but a code (or the words "NAICS code") was given.
    """
    tokens = query.split()
    has_number = any(re.fullmatch(_NUMERIC, token) for token in tokens)
    words = [
        token
        for token in tokens
        if not re.fullmatch(_NUMERIC, token)
        and re.search(r"\w", token)
        and not (has_number and _bare(token) in _CODE_WORDS)
    ]
    if all(_bare(word) in _CODE_WORDS for word in words):
        return ""
    return " ".join(words)


def _bare(token: str) -> str:
    return re.sub(r"\W", "", token).lower()


def _hits(scored: Sequence[ScoredDocument]) -> SccUpdate:
    """Rebuild documents from stored metadata; skip (and count) incomplete ones."""
    hits: list[SccHit] = []
    for item in scored:
        document = SccDocument.from_metadata(item.id, item.metadata)
        if document is not None:
            hits.append(SccHit(document=document, score=item.score))
    skipped = len(scored) - len(hits)
    warnings = [f"{skipped} retrieved entries had incomplete metadata and were skipped"]
    return SccUpdate(hits=hits, warnings=warnings if skipped else [])


class _Nodes:
    """Graph nodes over one index; each turns expected failures into warnings."""

    def __init__(
        self,
        index: VectorIndex,
        top_k: int,
        fingerprint: Callable[[], str],
        load: Callable[[], Sequence[IndexedDocument]],
    ) -> None:
        self._index = index
        self._top_k = top_k
        self._fingerprint = fingerprint
        self._load = load

    def validate(self, state: SccState) -> SccUpdate:
        given = state["query"].strip()
        if not given:
            return SccUpdate(warnings=["the industry description is empty"], failed=True)
        text = industry_text(given)
        if not text:
            return SccUpdate(warnings=[_CODE_ONLY.format(given=given)], failed=True)
        return SccUpdate(query=text)

    def ensure_index(self, state: SccState) -> SccUpdate:
        del state  # the index does not depend on the query
        try:
            self._index.ensure(self._fingerprint(), self._load)
        except RetrievalError as exc:
            return SccUpdate(warnings=[f"SCC index unavailable: {exc}"], failed=True)
        return SccUpdate()

    def retrieve(self, state: SccState) -> SccUpdate:
        try:
            scored = self._index.query(state["query"].strip(), self._top_k)
        except RetrievalError as exc:
            return SccUpdate(warnings=[f"SCC search failed: {exc}"], failed=True)
        return _hits(scored)


def _after_validate(state: SccState) -> str:
    return END if state["failed"] else "ensure_index"


def _after_ensure(state: SccState) -> str:
    return END if state["failed"] else "retrieve"


def build_scc_graph(
    index: VectorIndex,
    top_k: int,
    fingerprint: Callable[[], str],
    load: Callable[[], Sequence[IndexedDocument]],
) -> SccGraph:
    """Compile the retrieval graph.

    Args:
        index: Vector index to keep current and query (its embeddings are injected).
        top_k: Most hits returned.
        fingerprint: Returns the current source fingerprint (may raise ``SourceError``).
        load: Returns the documents to index; called only when the index must be rebuilt.

    Returns:
        A compiled graph; invoke it with ``{"query": ..., "hits": [], "warnings": [],
        "failed": False}``.
    """
    nodes = _Nodes(index, top_k, fingerprint, load)
    graph = StateGraph(SccState)
    graph.add_node("validate", nodes.validate)
    graph.add_node("ensure_index", nodes.ensure_index)
    graph.add_node("retrieve", nodes.retrieve)
    graph.add_edge(START, "validate")
    graph.add_conditional_edges("validate", _after_validate, ["ensure_index", END])
    graph.add_conditional_edges("ensure_index", _after_ensure, ["retrieve", END])
    graph.add_edge("retrieve", END)
    return graph.compile()
