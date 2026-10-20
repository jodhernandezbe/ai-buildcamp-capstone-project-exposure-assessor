"""Evidently adapter: score run records with LLM judges and write an HTML report.

Only this module imports ``evidently``. Each judge answers one narrow PASS/FAIL criterion
about the final report, with its reasoning kept.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.core.datasets import Descriptor
from evidently.descriptors import LLMEval
from evidently.llm.templates import BinaryClassificationPromptTemplate
from evidently.presets import TextEvals

from config.evaluation import EvaluationSettings
from evals.record import RunRecord

PASS_LABEL = "PASS"  # nosec B105 - a judge category, not a secret
FAIL_LABEL = "FAIL"
_REPORT_COLUMN = "report"


@dataclass(frozen=True)
class Judge:
    """One PASS/FAIL criterion about the final report."""

    name: str
    criteria: str


@dataclass(frozen=True)
class Verdict:
    """A judge's result for one record."""

    judge: str
    passed: bool
    reasoning: str


def _descriptor(judge: Judge, provider: str, model: str) -> Descriptor:
    template = BinaryClassificationPromptTemplate(
        criteria=judge.criteria,
        target_category=PASS_LABEL,
        non_target_category=FAIL_LABEL,
        uncertainty="non_target",  # type: ignore[arg-type]
        include_reasoning=True,
    )
    return LLMEval(
        _REPORT_COLUMN, provider=provider, model=model, template=template, alias=judge.name
    )


def _dataset(
    records: Sequence[RunRecord], judges: Sequence[Judge], provider: str, model: str
) -> Dataset:
    frame = pd.DataFrame(
        {
            "scenario_id": [r.scenario_id for r in records],
            "query": [r.query for r in records],
            _REPORT_COLUMN: [r.report for r in records],
        }
    )
    definition = DataDefinition(text_columns=["query", _REPORT_COLUMN])
    descriptors: list[Descriptor] = [_descriptor(j, provider, model) for j in judges]
    return Dataset.from_pandas(frame, data_definition=definition, descriptors=descriptors)


def _verdicts(row: Mapping[str, object], judges: Sequence[Judge]) -> tuple[Verdict, ...]:
    return tuple(
        Verdict(
            j.name,
            str(row.get(j.name, FAIL_LABEL)) == PASS_LABEL,
            str(row.get(f"{j.name} reasoning", "no reasoning returned")),
        )
        for j in judges
    )


def judge_records(
    records: Sequence[RunRecord], judges: Sequence[Judge], settings: EvaluationSettings
) -> tuple[tuple[Verdict, ...], ...]:
    """Score every record with every judge, write the HTML report, return the verdicts.

    Returns:
        One tuple of verdicts per record, in record order.
    """
    dataset = _dataset(records, judges, settings.judge_provider, settings.judge_model)
    report_dir = settings.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    Report([TextEvals()]).run(dataset).save_html(str(report_dir / f"evaluation-{stamp}.html"))
    frame = dataset.as_dataframe()
    rows: list[dict[str, object]] = frame.to_dict(orient="records")  # type: ignore[assignment]
    return tuple(_verdicts(row, judges) for row in rows)
