"""The scenario catalogue records the batch route beside the by-hand one."""

from __future__ import annotations

from evals.checks import ASSESSMENT
from evals.scenarios import CATALOGUE, FULL_ASSESSMENT, FULL_ASSESSMENT_CAS


def test_full_assessment_also_records_the_batch_route() -> None:
    assert [(e.tool, dict(e.args)) for e in FULL_ASSESSMENT.extra_calls] == [
        (ASSESSMENT, {"cas_number": FULL_ASSESSMENT_CAS})
    ]


def test_scenarios_without_extra_calls_record_none() -> None:
    others = [s for s in CATALOGUE if s is not FULL_ASSESSMENT]
    assert all(s.extra_calls == () for s in others)
