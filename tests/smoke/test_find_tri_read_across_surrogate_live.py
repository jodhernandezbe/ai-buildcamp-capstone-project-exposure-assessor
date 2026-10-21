"""Live smoke test for find_tri_read_across_surrogate (PubChem, the real MolDeBERTa model).

Run with ``uv run pytest -m smoke``. Needs the committed catalog
(the shards in ``data/tri_chemicals/``); the first run downloads the model (about 500 MB).

These cases guard the isotropy correction (design decision 7). Without it the embedding's raw
cosines sit in a narrow band: isohexane ranked an alcohol above n-hexane and caffeine was
admitted as in-domain. The assertions here are about *ranking* and about which chemicals the
applicability domain rejects, not about exact scores, so a better metric can only improve them.
"""

from __future__ import annotations

import pytest

from tools.informatics.read_across import find_tri_read_across_surrogate

pytestmark = pytest.mark.smoke


def test_isohexane_ranks_hexane_first() -> None:
    """107-83-5 is not on the TRI list; n-hexane (110-54-3) is its structural analogue.

    Its hybrid score sits just below the threshold (0.554 against 0.60), because ECFP4 rates
    a branched isomer as only modestly similar, so the tool reports it as outside the
    applicability domain. That limitation is documented; the ranking is what is pinned here.
    """
    result = find_tri_read_across_surrogate.invoke({"cas_number": "107-83-5"})
    assert result["resolution_method"] == "hybrid_read_across"
    assert result["query_smiles"] == "CCCC(C)C"
    assert result["query_mw"] == pytest.approx(86.18, abs=0.01)
    assert result["surrogate_tri_cas"] == "110-54-3"
    assert result["mw_scaling_factor"] == pytest.approx(1.0, abs=1e-3)
    assert result["hybrid_read_across_score"] is not None


def test_a_homologue_is_within_the_applicability_domain() -> None:
    """n-Heptane differs from n-hexane by one carbon, so it must be comfortably in domain."""
    result = find_tri_read_across_surrogate.invoke({"cas_number": "142-82-5"})
    assert result["surrogate_tri_cas"] == "110-54-3"
    assert result["within_applicability_domain"] is True


def test_a_chemical_unlike_the_tri_list_is_rejected() -> None:
    """Caffeine has no TRI analogue: the raw cosine admitted it, the centred one does not."""
    caffeine = find_tri_read_across_surrogate.invoke({"cas_number": "58-08-2"})
    isohexane = find_tri_read_across_surrogate.invoke({"cas_number": "107-83-5"})
    assert caffeine["within_applicability_domain"] is False
    assert caffeine["hybrid_read_across_score"] is not None
    assert isohexane["hybrid_read_across_score"] is not None
    assert caffeine["hybrid_read_across_score"] < isohexane["hybrid_read_across_score"]
    assert any("applicability domain" in w for w in caffeine["warnings"])


def test_listed_chemical_is_a_direct_match() -> None:
    result = find_tri_read_across_surrogate.invoke({"cas_number": "71-43-2"})
    assert result["is_direct_tri_match"] is True
    assert result["surrogate_name"]
    assert result["within_applicability_domain"] is True


def test_unknown_cas_is_a_warning_not_an_error() -> None:
    result = find_tri_read_across_surrogate.invoke({"cas_number": "9999-99-9"})
    assert result["resolution_method"] == "unresolved"
    assert result["warnings"]
