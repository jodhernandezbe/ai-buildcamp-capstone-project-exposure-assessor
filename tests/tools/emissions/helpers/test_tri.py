"""Tests for tools.emissions.helpers.tri (no network: an httpx mock transport)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace

import httpx
import pytest

from config.loader import TriSettings, load_tri_settings
from tools.emissions.helpers.tri import Row, TriFetcher, TriFetchError

CAS = "50-00-0"
SETTINGS = replace(
    load_tri_settings(),
    base_url="https://tri.test",
    release_path="/r/{casrn}/m/{medium}/rows/{start}:{end}/JSON",
    page_size=3,
    max_pages=4,
    delay_seconds=0.5,
    timeout_seconds=7.0,
    max_retries=2,
    backoff_seconds=1.0,
)

Handler = Callable[[httpx.Request], httpx.Response]


def _page(n: int, offset: int = 0) -> httpx.Response:
    return httpx.Response(200, json=[{"i": offset + k} for k in range(n)])


class Run:
    """A fetcher over a scripted handler, recording requests, waits and pages."""

    def __init__(self, handler: Handler, settings: TriSettings = SETTINGS) -> None:
        self.requests: list[httpx.Request] = []
        self.sleeps: list[float] = []
        self.pages: list[Sequence[Row]] = []

        def record(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return handler(request)

        client = httpx.Client(transport=httpx.MockTransport(record))
        self.fetcher = TriFetcher(settings, client, self.sleeps.append)

    def go(self, medium: str = "AIR STACK") -> bool:
        return self.fetcher.fetch(CAS, medium, self.pages.append)

    @property
    def urls(self) -> list[str]:
        return [str(r.url) for r in self.requests]


def _script(*responses: httpx.Response | Exception) -> Handler:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return handler


def test_pages_until_a_short_one() -> None:
    run = Run(_script(_page(3), _page(3, 3), _page(1, 6)))
    assert run.go() is False
    assert [len(p) for p in run.pages] == [3, 3, 1]
    assert run.urls == [
        "https://tri.test/r/50-00-0/m/AIR%20STACK/rows/0:2/JSON",
        "https://tri.test/r/50-00-0/m/AIR%20STACK/rows/3:5/JSON",
        "https://tri.test/r/50-00-0/m/AIR%20STACK/rows/6:8/JSON",
    ]


def test_empty_first_page_is_a_clean_end() -> None:
    run = Run(_script(_page(0)))
    assert run.go() is False
    assert run.pages == [[]]
    assert len(run.requests) == 1


def test_page_is_handed_over_as_it_arrives() -> None:
    seen: list[int] = []
    run = Run(_script(_page(3), _page(2, 3)))
    run.fetcher.fetch(CAS, "AIR STACK", lambda rows: seen.append(len(run.requests)))
    assert seen == [1, 2]


def test_waits_before_every_request() -> None:
    run = Run(_script(_page(3), _page(1, 3)))
    run.go()
    assert run.sleeps == [0.5, 0.5]


def test_every_request_has_the_timeout() -> None:
    run = Run(_script(_page(3), _page(0)))
    run.go()
    assert all(r.extensions["timeout"]["read"] == 7.0 for r in run.requests)


def test_page_cap_flags_possible_truncation() -> None:
    run = Run(_script(*[_page(3, 3 * i) for i in range(4)]))
    assert run.go() is True
    assert len(run.requests) == 4


def test_full_last_page_at_the_cap_is_flagged_even_if_complete() -> None:
    settings = replace(SETTINGS, max_pages=1)
    run = Run(_script(_page(3)), settings)
    assert run.go() is True


def test_throttled_then_success() -> None:
    run = Run(_script(httpx.Response(429), _page(2)))
    assert run.go() is False
    assert len(run.requests) == 2
    assert run.sleeps == [0.5, 1.0, 0.5]  # delay, backoff, delay


def test_backoff_doubles() -> None:
    run = Run(_script(httpx.Response(503), httpx.Response(500), _page(1)))
    run.go()
    assert run.sleeps == [0.5, 1.0, 0.5, 2.0, 0.5]


def test_retry_after_is_honoured() -> None:
    throttled = httpx.Response(429, headers={"Retry-After": "4"})
    run = Run(_script(throttled, _page(1)))
    run.go()
    assert run.sleeps == [0.5, 4.0, 0.5]


def test_retry_after_is_capped_by_the_timeout() -> None:
    throttled = httpx.Response(429, headers={"Retry-After": "86400"})
    run = Run(_script(throttled, _page(1)))
    run.go()
    assert run.sleeps == [0.5, 7.0, 0.5]


@pytest.mark.parametrize("header", ["soon", "-3", ""])
def test_unusable_retry_after_falls_back_to_backoff(header: str) -> None:
    run = Run(_script(httpx.Response(429, headers={"Retry-After": header}), _page(1)))
    run.go()
    assert run.sleeps == [0.5, 1.0, 0.5]


@pytest.mark.parametrize("failure", [httpx.ReadTimeout("slow"), httpx.ConnectError("down")])
def test_transport_failures_are_retried(failure: Exception) -> None:
    run = Run(_script(failure, _page(1)))
    assert run.go() is False
    assert len(run.requests) == 2


def test_malformed_json_is_retried() -> None:
    run = Run(_script(httpx.Response(200, content=b"<html>"), _page(1)))
    assert run.go() is False
    assert len(run.requests) == 2


def test_retries_exhausted_fails_without_partial_result_claims() -> None:
    run = Run(_script(*[httpx.Response(429)] * 3))
    with pytest.raises(TriFetchError, match="3 attempts.*HTTP 429"):
        run.go()
    assert len(run.requests) == 3


def test_failure_after_good_pages_still_raises() -> None:
    run = Run(_script(_page(3), *[httpx.Response(500)] * 3))
    with pytest.raises(TriFetchError):
        run.go()
    assert [len(p) for p in run.pages] == [3]  # the caller must discard what it folded in


def test_no_retries_when_configured_off() -> None:
    run = Run(_script(httpx.Response(429)), replace(SETTINGS, max_retries=0))
    with pytest.raises(TriFetchError):
        run.go()
    assert len(run.requests) == 1


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_other_client_errors_are_not_retried(status: int) -> None:
    run = Run(_script(httpx.Response(status)))
    with pytest.raises(TriFetchError, match=str(status)):
        run.go()
    assert len(run.requests) == 1


@pytest.mark.parametrize("body", [{"error": "x"}, "text", 5, [1, 2], [{"a": 1}, "x"], [[{"a": 1}]]])
def test_unexpected_shape_is_a_failure_not_data(body: object) -> None:
    run = Run(_script(httpx.Response(200, json=body)))
    with pytest.raises(TriFetchError, match="not a list of objects"):
        run.go()
    assert len(run.requests) == 1
    assert run.pages == []


def test_medium_and_cas_are_url_encoded() -> None:
    run = Run(_script(_page(0)))
    run.fetcher.fetch("50-00-0", "AIR/STACK X", run.pages.append)
    assert "m/AIR%2FSTACK%20X/rows" in run.urls[0]


def test_rows_are_plain_str_keyed_dicts() -> None:
    run = Run(_script(httpx.Response(200, json=[{"a": 1, "b": None}])))
    run.go()
    assert run.pages[0] == [{"a": 1, "b": None}]
