"""Tests for the [comptox.iris] settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.iris import parse_iris
from config.loader import get_comptox_settings, load_comptox_settings

KEYS = ("rfd", "rfc")


def _table(**changes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "path": "/i/{dtxsid}",
        "source": "S",
        "source_revised": "S, revised {revision}",
        "toxval_source": "T",
        "effects_field": "e",
        "revision_field": "r",
        "agreement_tolerance": 0.1,
        "fields": [{"key": "rfc", "field": "f", "units": ["u"]}],
    }
    return {"iris": {**base, **changes}}


def test_shipped_settings_rank_the_endpoint_for_rfd_and_rfc_only() -> None:
    iris = get_comptox_settings().iris
    assert iris is not None
    assert [(f.key, f.field) for f in iris.fields] == [("rfd", "rfdChronic"), ("rfc", "rfcChronic")]
    assert iris.toxval_source == get_comptox_settings().source_priority[0]
    assert iris.agreement_tolerance > 0


def test_url_is_the_base_url_and_the_path() -> None:
    url = get_comptox_settings().iris_by_dtxsid_url
    assert url is not None and url.endswith("/hazard/iris/search/by-dtxsid/{dtxsid}")


def test_absent_table_leaves_the_endpoint_unused() -> None:
    assert parse_iris({}, KEYS) is None


def test_valid_table_is_read() -> None:
    iris = parse_iris(_table(), KEYS)
    assert iris is not None and iris.fields[0].units == ("u",)


REFUSED: list[tuple[dict[str, object], str]] = [
    ({"path": "/i/none"}, "comptox.iris.path must contain {dtxsid}"),
    ({"source_revised": "S"}, "comptox.iris.source_revised must contain {revision}"),
    ({"source": ""}, "comptox.iris.source"),
    ({"agreement_tolerance": -1}, "comptox.iris.agreement_tolerance"),
    ({"agreement_tolerance": True}, "comptox.iris.agreement_tolerance"),
    ({"fields": []}, "comptox.iris.fields must be a non-empty list"),
    ({"fields": [{"key": "iur", "field": "f", "units": ["u"]}]}, "not a comptox"),
    ({"fields": [{"key": "rfc", "field": "f", "units": []}]}, "units"),
    (
        {"fields": [{"key": "rfc", "field": "f", "units": ["u"]}] * 2},
        "key listed twice",
    ),
]


@pytest.mark.parametrize(("change", "message"), REFUSED)
def test_invalid_table_is_refused(change: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_iris(_table(**change), KEYS)


def test_the_file_without_the_table_loads(tmp_path: Path) -> None:
    text = Path("config/settings.toml").read_text(encoding="utf-8")
    head, _, rest = text.partition("[comptox.iris]")
    tail = rest.split("[efservice]", 1)[1]
    path = tmp_path / "settings.toml"
    path.write_text(head + "[efservice]" + tail, encoding="utf-8")
    assert load_comptox_settings(path).iris is None
