"""Read-across tool: a CAS number -> the closest TRI chemical (itself, or a surrogate)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import httpx
from langchain_core.tools import tool

from commons.cas import format_cas
from config.read_across import ReadAcrossSettings, get_read_across_settings
from models.chemistry.similarity import (
    Scores,
    best_index,
    centered,
    cosine_similarities,
    hybrid_scores,
    tanimoto_similarities,
)
from tools.http import RetryingClient
from tools.informatics.helpers.read_across.catalog import Catalog, filter_candidates, get_catalog
from tools.informatics.helpers.read_across.moldeberta import SmilesEmbedder, lazy_default_embedder
from tools.informatics.helpers.read_across.pubchem import PubchemCompound, fetch_compound
from tools.informatics.helpers.read_across.structure import Structure, describe
from tools.schemas import ReadAcrossMatch

_DECIMALS = 4  # reported scores; the domain check uses the unrounded score


@dataclass(frozen=True)
class ReadAcrossServices:
    """The collaborators one lookup needs (injected; defaults are built at the edge)."""

    catalog: Catalog
    embedder: SmilesEmbedder
    pubchem: RetryingClient
    settings: ReadAcrossSettings


@dataclass(frozen=True)
class _Query:
    """A resolved query chemical."""

    cas: str
    structure: Structure
    molecular_weight: float | None


def _unresolved(query_cas: str, warnings: list[str]) -> ReadAcrossMatch:
    return {
        "query_cas": query_cas,
        "query_smiles": None,
        "query_mw": None,
        "is_direct_tri_match": False,
        "surrogate_tri_cas": None,
        "surrogate_name": None,
        "surrogate_smiles": None,
        "surrogate_mw": None,
        "moldeberta_cosine_sim": None,
        "morgan_tanimoto_sim": None,
        "hybrid_read_across_score": None,
        "mw_scaling_factor": None,
        "within_applicability_domain": False,
        "resolution_method": "unresolved",
        "warnings": warnings,
    }


def _direct(cas: str, catalog: Catalog, row: int, warnings: list[str]) -> ReadAcrossMatch:
    weight = float(catalog.molecular_weights[row])
    return {
        "query_cas": cas,
        "query_smiles": catalog.smiles[row],
        "query_mw": weight,
        "is_direct_tri_match": True,
        "surrogate_tri_cas": cas,
        "surrogate_name": catalog.names[row],
        "surrogate_smiles": catalog.smiles[row],
        "surrogate_mw": weight,
        "moldeberta_cosine_sim": 1.0,
        "morgan_tanimoto_sim": 1.0,
        "hybrid_read_across_score": 1.0,
        "mw_scaling_factor": 1.0,
        "within_applicability_domain": True,
        "resolution_method": "direct_tri_catalog_match",
        "warnings": warnings,
    }


def _positive(value: float) -> bool:
    return math.isfinite(value) and value > 0


def _scaling_factor(query_mw: float | None, surrogate_mw: float) -> float | None:
    if query_mw is None or not _positive(query_mw) or not _positive(surrogate_mw):
        return None
    return query_mw / surrogate_mw


def _resolve(cas: str, services: ReadAcrossServices, warnings: list[str]) -> _Query | None:
    """Look the query up on PubChem and parse its structure; None (with a warning) if not."""
    found = fetch_compound(cas, services.pubchem, services.settings.pubchem)
    if not isinstance(found, PubchemCompound):
        warnings.append(f"the structure of {cas} could not be resolved: {found}")
        return None
    structure = describe(found.smiles, services.settings.fingerprint)
    if structure is None:
        warnings.append(f"the SMILES PubChem gives for {cas} ({found.smiles!r}) cannot be parsed")
        return None
    if found.molecular_weight is None:
        warnings.append(f"molecular weight of {cas} not found in PubChem")
    return _Query(cas, structure, found.molecular_weight)


def _similarities(
    query: _Query, candidates: Catalog, services: ReadAcrossServices
) -> tuple[Scores, Scores, Scores] | str:
    """Cosine, Tanimoto and hybrid score of the query against every candidate.

    The embedding is centred on the catalog's mean embedding first, because the model's raw
    cosines sit in a narrow band that does not separate analogues (see design decision 7).
    The same mean is used for the catalog rows, so the comparison is symmetric.

    Returns:
        The three score arrays, or a reason (str) why the query cannot be compared.
    """
    vector = services.embedder(query.structure.smiles)
    try:
        corrected = centered(vector, candidates.mean_embedding)
    except ValueError as exc:
        return f"the embedding of {query.cas} carries no direction once centred: {exc}"
    cosine = cosine_similarities(corrected, candidates.centered_embeddings)
    tanimoto = tanimoto_similarities(query.structure.bits, candidates.bits)
    return cosine, tanimoto, hybrid_scores(cosine, tanimoto, services.settings.alpha)


def _no_surrogate(query: _Query, warnings: list[str]) -> ReadAcrossMatch:
    """A resolved query that could not be matched: the chemical is reported, no surrogate is."""
    return {
        **_unresolved(query.cas, warnings),
        "query_smiles": query.structure.smiles,
        "query_mw": query.molecular_weight,
    }


def _best_match(
    query: _Query,
    candidates: Catalog,
    services: ReadAcrossServices,
    cosine: Scores,
    tanimoto: Scores,
    hybrid: Scores,
) -> ReadAcrossMatch:
    """Package the highest-scoring candidate as the result."""
    row = best_index(hybrid)
    surrogate_mw = float(candidates.molecular_weights[row])
    return {
        **_no_surrogate(query, []),
        "surrogate_tri_cas": candidates.cas[row],
        "surrogate_name": candidates.names[row],
        "surrogate_smiles": candidates.smiles[row],
        "surrogate_mw": surrogate_mw,
        "moldeberta_cosine_sim": round(float(cosine[row]), _DECIMALS),
        "morgan_tanimoto_sim": round(float(tanimoto[row]), _DECIMALS),
        "hybrid_read_across_score": round(float(hybrid[row]), _DECIMALS),
        "mw_scaling_factor": _scaling_factor(query.molecular_weight, surrogate_mw),
        "within_applicability_domain": bool(hybrid[row] >= services.settings.min_hybrid_score),
        "resolution_method": "hybrid_read_across",
    }


def _score(
    query: _Query, candidates: Catalog, services: ReadAcrossServices
) -> ReadAcrossMatch | str:
    """The best candidate for a resolved query, or a reason why it could not be scored."""
    scores = _similarities(query, candidates, services)
    if isinstance(scores, str):
        return scores
    return _best_match(query, candidates, services, *scores)


def _candidates(
    services: ReadAcrossServices,
    require_benchmarks: bool,
    naics_prefix: str | None,
) -> tuple[Catalog, list[str]]:
    """The candidate surrogates left by the optional filters, with any filter warnings."""
    return filter_candidates(
        services.catalog, require_benchmarks=require_benchmarks, naics_prefix=naics_prefix
    )


def _domain_warning(match: ReadAcrossMatch, threshold: float) -> str | None:
    if match["within_applicability_domain"]:
        return None
    return (
        f"hybrid score {match['hybrid_read_across_score']} is below the applicability-domain "
        f"threshold {threshold}: {match['surrogate_tri_cas']} is outside the applicability "
        "domain and must not be used for read-across without expert justification"
    )


def find_surrogate(
    cas_number: str,
    services: ReadAcrossServices,
    *,
    require_toxicity_benchmarks: bool = False,
    sector_naics_prefix: str | None = None,
) -> ReadAcrossMatch:
    """Find the TRI chemical closest to ``cas_number`` (see the tool for the full contract).

    Returns:
        Every field of ``ReadAcrossMatch``; values that could not be obtained are None and
        ``warnings`` says why. Nothing is raised for a data problem.
    """
    cas = format_cas(cas_number)
    if cas is None:
        return _unresolved(cas_number.strip(), [f"CAS number {cas_number!r} is not valid"])
    candidates, warnings = _candidates(services, require_toxicity_benchmarks, sector_naics_prefix)
    row = candidates.index_of(cas)
    if row is not None:
        return _direct(cas, candidates, row, warnings)
    query = _resolve(cas, services, warnings)
    if query is None:
        return _unresolved(cas, warnings)
    match = _score(query, candidates, services)
    if isinstance(match, str):
        return _no_surrogate(query, [*warnings, match])
    domain = _domain_warning(match, services.settings.min_hybrid_score)
    match["warnings"] = warnings + ([domain] if domain else [])
    return match


@lru_cache(maxsize=1)
def _services() -> ReadAcrossServices:
    """Build the default collaborators once (the model itself loads on first embedding)."""
    settings = get_read_across_settings()
    return ReadAcrossServices(
        catalog=get_catalog(settings),
        embedder=lazy_default_embedder(settings.model),
        pubchem=RetryingClient(settings.pubchem, httpx.Client()),
        settings=settings,
    )


@tool
def find_tri_read_across_surrogate(
    cas_number: str,
    require_toxicity_benchmarks: bool = False,
    sector_naics_prefix: str | None = None,
) -> ReadAcrossMatch:
    """Find the TRI chemical most similar in structure to a chemical (read-across surrogate).

    Purpose:
        Applies only to a chemical already identified by a CAS number the user gave; it never
        identifies a chemical from its name. Use it when that chemical is not on the TRI list or
        has no inhalation benchmark: it names the most similar TRI chemical, whose data may stand
        in for it (read-across), chosen by structural similarity.

        How to read the result:
        - `is_direct_tri_match` true: the chemical is itself on the TRI list; no surrogate is
          needed.
        - Otherwise, report `hybrid_read_across_score` and `within_applicability_domain` with
          anything you take from the surrogate. A surrogate's benchmark is a read-across
          estimate, not a measured value for the query chemical; say so.
        - `within_applicability_domain` false: the surrogate is too dissimilar. Do not use its
          values, or if you show them, say plainly that they are outside the applicability
          domain.
        - A null surrogate means none could be found; report that, do not guess one.

    Args:
        cas_number: CAS registry number as the user gave it, e.g. "107-83-5" (hyphens
            optional). Never a number recalled from a chemical's name: if the user gave only
            a name, ask for the CAS number instead of calling this tool.
        require_toxicity_benchmarks: True to consider only TRI chemicals known to have an
            IRIS benchmark (ignored, with a warning, if that is not known).
        sector_naics_prefix: Optional NAICS code prefix (e.g. "325") to consider only TRI
            chemicals reported by that industry (ignored, with a warning, if unknown or if
            no chemical matches).

    Returns:
        A dict with:
        - query_cas, query_smiles, query_mw: the query chemical (MW in g/mol)
        - is_direct_tri_match: the query chemical is itself on the TRI list
        - surrogate_tri_cas, surrogate_name, surrogate_smiles, surrogate_mw: the closest
          TRI chemical (MW in g/mol); null if none could be found
        - moldeberta_cosine_sim: embedding similarity, -1 to 1
        - morgan_tanimoto_sim: shared structural fragments, 0 to 1
        - hybrid_read_across_score: the combined score the choice is based on, 1 = identical
        - mw_scaling_factor: query_mw / surrogate_mw. It is reported, never applied: a
          surrogate benchmark in mg/m^3 can be put on a molar basis by multiplying it by
          this factor; say so if you do. Null if a molecular weight is missing
        - within_applicability_domain: whether the score reaches the configured threshold
        - resolution_method: "direct_tri_catalog_match", "hybrid_read_across" or "unresolved"
        - warnings: why a value is null, filters not applied, or that the surrogate is
          outside the applicability domain
    """
    return find_surrogate(
        cas_number,
        _services(),
        require_toxicity_benchmarks=require_toxicity_benchmarks,
        sector_naics_prefix=sector_naics_prefix,
    )
