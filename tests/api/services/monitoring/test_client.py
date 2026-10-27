"""Tests for the Logfire query wrapper: every API failure becomes a state-level exception."""

from __future__ import annotations

from types import TracebackType
from typing import Self

import httpx
import pytest
from logfire.query_client import QueryExecutionError, UnexpectedResponseError
from pydantic import SecretStr

from api.services.monitoring import client as client_module
from api.services.monitoring.client import (
    MonitoringUnauthorizedError,
    MonitoringUnavailableError,
    logfire_query,
)
from tests.api.services.monitoring.factories import settings

pytestmark = pytest.mark.anyio
TOKEN = SecretStr("pylf_v1_us_" + "t" * 40)  # pragma: allowlist secret
SETTINGS = settings()


class FakeApi:
    """Stands in for the Logfire async client; raises ``failure`` or answers with ``rows``."""

    failure: Exception | None = None
    rows: list[dict[str, object]] = []
    seen: dict[str, object] = {}

    def __init__(self, read_token: str, *, timeout: httpx.Timeout) -> None:
        FakeApi.seen = {"token": read_token, "timeout": timeout}

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        return None

    async def info(self) -> dict[str, str]:
        if FakeApi.failure:
            raise FakeApi.failure
        return {"organization_name": "acme", "project_name": "assessor"}

    async def query_json_rows(self, **kwargs: object) -> dict[str, object]:
        if FakeApi.failure:
            raise FakeApi.failure
        FakeApi.seen.update(kwargs)
        return {"rows": FakeApi.rows}


@pytest.fixture(autouse=True)
def fake_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "AsyncLogfireQueryClient", FakeApi)
    FakeApi.failure, FakeApi.rows, FakeApi.seen = None, [], {}


async def test_rows_use_the_token_the_timeout_the_window_and_the_row_cap() -> None:
    FakeApi.rows = [{"a": 1}]
    async with logfire_query(TOKEN, SETTINGS) as query:
        assert await query.rows("select 1", 24) == [{"a": 1}]
        project = await query.project()
    assert (project.organization, project.name) == ("acme", "assessor")
    assert FakeApi.seen["token"] == TOKEN.get_secret_value()
    assert FakeApi.seen["limit"] == SETTINGS.max_rows and FakeApi.seen["sql"] == "select 1"
    assert FakeApi.seen["timeout"] == httpx.Timeout(SETTINGS.query_timeout_seconds)


@pytest.mark.parametrize("status", [401, 403])
async def test_a_refused_token_is_unauthorized(status: int) -> None:
    FakeApi.failure = UnexpectedResponseError(f"Unexpected response status code {status}: 'no'")
    async with logfire_query(TOKEN, SETTINGS) as query:
        with pytest.raises(MonitoringUnauthorizedError):
            await query.rows("select 1", 1)


@pytest.mark.parametrize(
    "failure",
    [
        httpx.ReadTimeout("slow"),
        httpx.ConnectError("down"),
        UnexpectedResponseError("Unexpected response status code 429: 'later'"),
        UnexpectedResponseError("Unexpected response status code 503: 'x'"),
        QueryExecutionError("bad sql"),
    ],
)
async def test_every_other_failure_is_unavailable_and_never_echoes_the_cause(
    failure: Exception,
) -> None:
    FakeApi.failure = failure
    async with logfire_query(TOKEN, SETTINGS) as query:
        with pytest.raises(MonitoringUnavailableError) as raised:
            await query.rows("select 1", 1)
    assert str(failure) not in str(raised.value)
    assert TOKEN.get_secret_value() not in str(raised.value)


async def test_a_failing_info_call_is_translated_too() -> None:
    FakeApi.failure = httpx.ReadTimeout("slow")
    async with logfire_query(TOKEN, SETTINGS) as query:
        with pytest.raises(MonitoringUnavailableError):
            await query.project()
