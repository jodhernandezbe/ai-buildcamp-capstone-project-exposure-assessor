"""Tests for reading the TRI chemical list and keeping its discrete, listed chemicals."""

from __future__ import annotations

from dataclasses import replace

import httpx
import pytest

from config.efservice import load_efservice_settings
from config.read_across import TriListSettings, load_read_across_settings
from tests.tools.informatics.read_across_fakes import Server, answer
from tools.informatics.helpers.read_across.tri_list import (
    DELISTED,
    DUPLICATE,
    GROUP,
    TriChemical,
    TriListError,
    discrete_chemicals,
    fetch_rows,
)

EFSERVICE = load_efservice_settings()
TRI = load_read_across_settings().tri_list


def _row(cas: str, name: str = "x", inactive: str | None = "9999") -> dict[str, object]:
    return {"cas_registry_number": cas, "chem_name": name, "inactive_date": inactive}


def _fetch(server: Server, settings: TriListSettings = TRI) -> list[dict[str, object]]:
    return fetch_rows(server.client, EFSERVICE, settings)


def test_single_page() -> None:
    server = Server(answer([_row("50-00-0")]))
    assert len(_fetch(server)) == 1
    assert server.urls == [EFSERVICE.url("/tri_chem_info/rows/0:1999/JSON")]


def test_full_page_requests_the_next() -> None:
    pages = {"0:1": [_row("50-00-0"), _row("71-43-2")], "2:3": [_row("79-01-6")]}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=pages[request.url.path.split("/")[-2]])

    server = Server(handler)
    rows = _fetch(server, replace(TRI, page_size=2))
    assert [r["cas_registry_number"] for r in rows] == ["50-00-0", "71-43-2", "79-01-6"]
    assert len(server.urls) == 2


def test_endless_list_is_an_error() -> None:
    server = Server(answer([_row("50-00-0")]))
    with pytest.raises(TriListError, match="did not end"):
        _fetch(server, replace(TRI, page_size=1))


def test_missing_field_is_an_error() -> None:
    server = Server(answer([{"cas_registry_number": "50-00-0", "chem_name": "x"}]))
    with pytest.raises(TriListError, match="'inactive_date' is missing"):
        _fetch(server)


@pytest.mark.parametrize("body", [{"error": "x"}, ["not a row"]])
def test_malformed_answer_is_an_error(body: object) -> None:
    with pytest.raises(TriListError, match="unexpected answer"):
        _fetch(Server(answer(body)))


def test_unreachable_is_an_error() -> None:
    with pytest.raises(TriListError, match="could not be read"):
        _fetch(Server(answer({}, 500)))


def test_groups_delisted_and_duplicates_dropped() -> None:
    rows = [
        _row("50-00-0", "Formaldehyde"),
        _row("N420", "Lead compounds"),
        _row("MIXTURE"),
        _row("TRD SECRT"),
        _row("NA"),
        _row("7647-01-0", "Hydrochloric acid", inactive="1994"),
        _row("50-00-0", "Formaldehyde again"),
        _row("71-43-2", "  "),
        _row("79-01-6", "Trichloroethylene", inactive=None),
    ]
    kept = discrete_chemicals(rows, TRI)
    assert kept.chemicals == (
        TriChemical("50-00-0", "Formaldehyde"),
        TriChemical("71-43-2", "71-43-2"),
        TriChemical("79-01-6", "Trichloroethylene"),
    )
    assert kept.dropped == {GROUP: 4, DELISTED: 1, DUPLICATE: 1}


def test_delisted_kept_when_configured() -> None:
    rows = [_row("7647-01-0", "Hydrochloric acid", inactive="1994")]
    kept = discrete_chemicals(rows, replace(TRI, keep_delisted=True))
    assert [c.cas for c in kept.chemicals] == ["7647-01-0"]


def test_bare_digit_cas_is_hyphenated() -> None:
    kept = discrete_chemicals([_row("71432")], TRI)
    assert kept.chemicals[0].cas == "71-43-2"
