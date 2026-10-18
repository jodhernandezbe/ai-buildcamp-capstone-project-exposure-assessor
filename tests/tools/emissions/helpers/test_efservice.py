"""Tests for tools.emissions.helpers.efservice (no network: an httpx mock transport)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import httpx
import pytest

from config.efservice import EfserviceSettings, load_efservice_settings
from tools.emissions.helpers.efservice import EfserviceClient, EfserviceError, Row

SETTINGS = replace(
    load_efservice_settings(),
    base_url="https://ef.test/",
    delay_seconds=0.5,
    timeout_seconds=7.0,
    max_retries=2,
    backoff_seconds=1.0,
)

Handler = Callable[[httpx.Request], httpx.Response]


def _ok(n: int = 1) -> httpx.Response:
    return httpx.Response(200, json=[{"i": k} for k in range(n)])


class Run:
    """A client over a scripted handler, recording requests and waits."""

    def __init__(self, handler: Handler, settings: EfserviceSettings = SETTINGS) -> None:
        self.requests: list[httpx.Request] = []
        self.sleeps: list[float] = []

        def record(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return handler(request)

        http = httpx.Client(transport=httpx.MockTransport(record))
        self.client = EfserviceClient(settings, http, self.sleeps.append)

    def go(self, path: str = "/q/JSON") -> list[Row]:
        return self.client.get_rows(path)


def _script(*responses: httpx.Response | Exception) -> Handler:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return handler


def test_url_is_base_plus_path() -> None:
    run = Run(_script(_ok()))
    run.go("/a/b/JSON")
    assert [str(r.url) for r in run.requests] == ["https://ef.test/a/b/JSON"]


def test_rows_are_plain_str_keyed_dicts() -> None:
    run = Run(_script(httpx.Response(200, json=[{"a": 1, "b": None}])))
    assert run.go() == [{"a": 1, "b": None}]


def test_empty_list_is_a_result() -> None:
    assert Run(_script(_ok(0))).go() == []


def test_waits_before_every_request() -> None:
    run = Run(_script(_ok()))
    run.go()
    assert run.sleeps == [0.5]


def test_every_request_has_the_timeout() -> None:
    run = Run(_script(_ok()))
    run.go()
    assert run.requests[0].extensions["timeout"]["read"] == 7.0


def test_throttled_then_success() -> None:
    run = Run(_script(httpx.Response(429), _ok(2)))
    assert len(run.go()) > 0
    assert len(run.requests) == 2
    assert run.sleeps == [0.5, 1.0, 0.5]  # delay, backoff, delay


def test_backoff_doubles() -> None:
    run = Run(_script(httpx.Response(503), httpx.Response(500), _ok(1)))
    run.go()
    assert run.sleeps == [0.5, 1.0, 0.5, 2.0, 0.5]


def test_retry_after_is_honoured() -> None:
    throttled = httpx.Response(429, headers={"Retry-After": "4"})
    run = Run(_script(throttled, _ok(1)))
    run.go()
    assert run.sleeps == [0.5, 4.0, 0.5]


def test_retry_after_is_capped_by_the_timeout() -> None:
    throttled = httpx.Response(429, headers={"Retry-After": "86400"})
    run = Run(_script(throttled, _ok(1)))
    run.go()
    assert run.sleeps == [0.5, 7.0, 0.5]


@pytest.mark.parametrize("header", ["soon", "-3", ""])
def test_unusable_retry_after_falls_back_to_backoff(header: str) -> None:
    run = Run(_script(httpx.Response(429, headers={"Retry-After": header}), _ok(1)))
    run.go()
    assert run.sleeps == [0.5, 1.0, 0.5]


@pytest.mark.parametrize("failure", [httpx.ReadTimeout("slow"), httpx.ConnectError("down")])
def test_transport_failures_are_retried(failure: Exception) -> None:
    run = Run(_script(failure, _ok(1)))
    assert len(run.go()) > 0
    assert len(run.requests) == 2


def test_malformed_json_is_retried() -> None:
    run = Run(_script(httpx.Response(200, content=b"<html>"), _ok(1)))
    assert len(run.go()) > 0
    assert len(run.requests) == 2


def test_retries_exhausted_fails() -> None:
    run = Run(_script(*[httpx.Response(429)] * 3))
    with pytest.raises(EfserviceError, match="3 attempts.*HTTP 429"):
        run.go()
    assert len(run.requests) == 3


def test_no_retries_when_configured_off() -> None:
    run = Run(_script(httpx.Response(429)), replace(SETTINGS, max_retries=0))
    with pytest.raises(EfserviceError):
        run.go()
    assert len(run.requests) == 1


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_other_client_errors_are_not_retried(status: int) -> None:
    run = Run(_script(httpx.Response(status)))
    with pytest.raises(EfserviceError, match=str(status)):
        run.go()
    assert len(run.requests) == 1


@pytest.mark.parametrize("body", [{"error": "x"}, "text", 5, [1, 2], [{"a": 1}, "x"], [[{"a": 1}]]])
def test_unexpected_shape_is_a_failure_not_data(body: object) -> None:
    run = Run(_script(httpx.Response(200, json=body)))
    with pytest.raises(EfserviceError, match="not a list of objects"):
        run.go()
    assert len(run.requests) == 1
