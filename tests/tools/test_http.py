"""Tests for tools.http (no network: an httpx mock transport)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import httpx
import pytest

from tools.http import HttpRequestError, RetryingClient

Handler = Callable[[httpx.Request], httpx.Response]


@dataclass(frozen=True)
class Policy:
    delay_seconds: float = 0.5
    timeout_seconds: float = 7.0
    max_retries: int = 2
    backoff_seconds: float = 1.0


DEFAULT = Policy()


class Run:
    def __init__(self, *responses: httpx.Response | Exception, policy: Policy = DEFAULT) -> None:
        self.requests: list[httpx.Request] = []
        self.sleeps: list[float] = []
        queue = list(responses)

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        http = httpx.Client(transport=httpx.MockTransport(handler))
        self.client = RetryingClient(policy, http, self.sleeps.append)

    def get(self, params: dict[str, str | int | float] | None = None) -> object:
        return self.client.get_json("https://svc.test/q", params)


def test_returns_the_decoded_body_of_any_shape() -> None:
    assert Run(httpx.Response(200, json={"hourly": {"a": [1]}})).get() == {"hourly": {"a": [1]}}
    assert Run(httpx.Response(200, json=[1, 2])).get() == [1, 2]


def test_a_json_null_is_a_result_not_a_failure() -> None:
    run = Run(httpx.Response(200, content=b"null"))
    assert run.get() is None
    assert len(run.requests) == 1


def test_query_parameters_are_sent() -> None:
    run = Run(httpx.Response(200, json={}))
    run.get({"latitude": 41.5, "hourly": "a,b", "year": 2022})
    assert dict(run.requests[0].url.params) == {"latitude": "41.5", "hourly": "a,b", "year": "2022"}


def test_waits_the_delay_before_every_request() -> None:
    run = Run(httpx.Response(200, json={}))
    run.get()
    assert run.sleeps == [0.5]


def test_every_request_has_the_timeout() -> None:
    run = Run(httpx.Response(200, json={}))
    run.get()
    assert run.requests[0].extensions["timeout"]["read"] == 7.0


def test_backoff_doubles_between_retries() -> None:
    run = Run(httpx.Response(503), httpx.Response(500), httpx.Response(200, json={}))
    run.get()
    assert run.sleeps == [0.5, 1.0, 0.5, 2.0, 0.5]


def test_retry_after_is_honoured_up_to_the_timeout() -> None:
    run = Run(httpx.Response(429, headers={"Retry-After": "86400"}), httpx.Response(200, json={}))
    run.get()
    assert run.sleeps == [0.5, 7.0, 0.5]


@pytest.mark.parametrize("failure", [httpx.ReadTimeout("slow"), httpx.ConnectError("down")])
def test_transport_failures_are_retried(failure: Exception) -> None:
    run = Run(failure, httpx.Response(200, json={}))
    assert run.get() == {}
    assert len(run.requests) == 2


def test_malformed_json_is_retried() -> None:
    run = Run(httpx.Response(200, content=b"<html>"), httpx.Response(200, json={}))
    assert run.get() == {}
    assert len(run.requests) == 2


def test_retries_exhausted() -> None:
    run = Run(*[httpx.Response(429)] * 3)
    with pytest.raises(HttpRequestError, match="3 attempts.*HTTP 429"):
        run.get()
    assert len(run.requests) == 3


def test_no_retries_when_configured_off() -> None:
    run = Run(httpx.Response(429), policy=Policy(max_retries=0))
    with pytest.raises(HttpRequestError, match="1 attempts"):
        run.get()


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_other_client_errors_are_not_retried(status: int) -> None:
    run = Run(httpx.Response(status))
    with pytest.raises(HttpRequestError, match=str(status)):
        run.get()
    assert len(run.requests) == 1
