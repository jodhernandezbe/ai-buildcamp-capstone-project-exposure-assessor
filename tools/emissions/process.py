"""SCC process-context tool: industry description -> candidate SCC process descriptions."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from tools.emissions.rag.documents import SccHit
from tools.emissions.rag.errors import EmbeddingError
from tools.emissions.rag.retriever import SccRetriever, default_scc_retriever
from tools.schemas import SccLookupResult, SccMatch

logger = logging.getLogger(__name__)


def _get_retriever() -> SccRetriever:
    """Return the default retriever (the edge where the collaborator is built)."""
    return default_scc_retriever()


def _match(hit: SccHit) -> SccMatch:
    document = hit.document
    return SccMatch(
        scc=document.scc,
        level_one=document.level_one,
        level_two=document.level_two,
        level_three=document.level_three,
        level_four=document.level_four,
        sector=document.sector,
        score=round(hit.score, 4),
    )


@tool
def lookup_scc_process_description(naics_description: str) -> SccLookupResult:
    """Find the EPA Source Classification Codes (SCCs) that best match an industry.

    Purpose:
        A NAICS code says what a facility makes, not which physical process emits. Use this
        with the facility's NAICS (industry) description to learn the likely emitting
        processes, described in plain text from broad (level one) to specific (level four),
        e.g. a refinery's "Catalytic Cracking Unit". Use it to explain the source to the
        user and to pick an SCC for `fetch_stack_parameters_from_scc`. Matches come from a
        semantic search over EPA's SCC list (active point-source codes only); they are
        candidates ranked by similarity, not an official NAICS-to-SCC crosswalk, so judge
        them against what is known about the facility.

    Args:
        naics_description: NAICS industry title or description, e.g. "Petroleum Refineries".

    Returns:
        A dict with:
        - matches: best first, each with
          - scc: Source Classification Code (digits)
          - level_one .. level_four: process description, broad to specific
          - sector: EPA emission sector
          - score: similarity, 0 (unrelated) to 1 (identical wording)
        - warnings: why matches are missing (empty description, index or embedding service
          unavailable); empty when the search ran normally
    """
    try:
        retriever = _get_retriever()
    except EmbeddingError as exc:
        logger.warning("lookup_scc_process_description: %s", exc)
        return SccLookupResult(matches=[], warnings=[f"SCC lookup unavailable: {exc}"])
    lookup = retriever.lookup(naics_description)
    for warning in lookup.warnings:
        logger.warning("lookup_scc_process_description: %s", warning)
    return SccLookupResult(matches=[_match(h) for h in lookup.hits], warnings=list(lookup.warnings))
