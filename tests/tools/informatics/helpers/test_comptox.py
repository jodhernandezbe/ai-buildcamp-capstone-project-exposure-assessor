"""Tests for tools.informatics.helpers.comptox (no network, synthetic payloads)."""

from __future__ import annotations

import httpx
import pytest

from config.loader import ComptoxSettings, PropertySpec
from tools.informatics.helpers.comptox import ComptoxLookup

ENV = {"TEST_KEY_VAR": "test-key"}


def _settings(*extra: PropertySpec) -> ComptoxSettings:
    return ComptoxSettings(
        base_url="https://ctx.test/api",
        dtxsid_by_smiles_path="/s?smiles={smiles}",
        properties_by_dtxsid_path="/p/{dtxsid}",
        api_key_header="x-test-key",  # pragma: allowlist secret
        api_key_env_var="TEST_KEY_VAR",  # pragma: allowlist secret
        delay_seconds=0.5,
        timeout_seconds=1.0,
        properties=(
            PropertySpec("vapor_pressure", "Vapor Pressure"),
            PropertySpec("density", "Density"),
            *extra,
        ),
    )


def _entry(
    name: str, unit: str = "u", experimental: float | None = None, predicted: float | None = None
) -> dict[str, object]:
    return {
        "propName": name,
        "unit": unit,
        "experimentalMedian": experimental,
        "predictedMedian": predicted,
    }


def _lookup(
    summary: object,
    *,
    dtxsid_status: int = 200,
    dtxsid_body: object = None,
    summary_status: int = 200,
    env: dict[str, str] | None = None,
    settings: ComptoxSettings | None = None,
    fail: Exception | None = None,
    sleeps: list[float] | None = None,
) -> tuple[ComptoxLookup, list[httpx.Request]]:
    requests: list[httpx.Request] = []
    body = [{"dtxsid": "DTXSID0"}] if dtxsid_body is None else dtxsid_body

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if fail is not None:
            raise fail
        if request.url.path.startswith("/api/s"):
            return httpx.Response(dtxsid_status, json=body)
        if isinstance(summary, str):
            return httpx.Response(summary_status, text=summary)
        return httpx.Response(summary_status, json=summary)

    client = httpx.Client(transport=httpx.MockTransport(respond))
    record = sleeps if sleeps is not None else []
    lookup = ComptoxLookup(
        settings or _settings(),
        client,
        sleep=record.append,
        environ=ENV if env is None else env,
    )
    return lookup, requests


def test_experimental_preferred_over_predicted() -> None:
    summary = [
        _entry("Vapor Pressure", "unit-a", experimental=1.5, predicted=9.0),
        _entry("Density", "unit-b", experimental=2.5, predicted=8.0),
    ]
    lookup, _ = _lookup(summary)
    assert lookup.get_properties("CCO") == {
        "vapor_pressure": {"value": 1.5, "unit": "unit-a", "source": "experimental"},
        "density": {"value": 2.5, "unit": "unit-b", "source": "experimental"},
    }


def test_predicted_fallback_and_unit_passthrough() -> None:
    lookup, _ = _lookup([_entry("Vapor Pressure", "mmHg", predicted=3.0)])
    assert lookup.get_properties("CCO") == {
        "vapor_pressure": {"value": 3.0, "unit": "mmHg", "source": "predicted"}
    }


def test_zero_experimental_is_a_value() -> None:
    lookup, _ = _lookup([_entry("Density", experimental=0.0, predicted=5.0)])
    assert lookup.get_properties("CCO")["density"]["value"] == 0.0


def test_missing_or_empty_properties_omitted() -> None:
    lookup, _ = _lookup([_entry("Vapor Pressure"), _entry("Boiling Point", experimental=1.0)])
    assert lookup.get_properties("CCO") == {}


def test_unconfigured_ignored_and_extra_configured_picked_up() -> None:
    summary = [_entry("Density", experimental=1.0), _entry("Melting Point", "c", experimental=7.0)]
    lookup, _ = _lookup(summary)
    assert set(lookup.get_properties("CCO")) == {"density"}
    extended, _ = _lookup(
        summary, settings=_settings(PropertySpec("melting_point", "Melting Point"))
    )
    assert set(extended.get_properties("CCO")) == {"density", "melting_point"}


def test_requests_use_quoted_smiles_header_and_delay() -> None:
    sleeps: list[float] = []
    lookup, requests = _lookup([_entry("Density", experimental=1.0)], sleeps=sleeps)
    lookup.get_properties("C(=O)#N/C")
    assert str(requests[0].url) == "https://ctx.test/api/s?smiles=C%28%3DO%29%23N%2FC"
    assert str(requests[1].url) == "https://ctx.test/api/p/DTXSID0"
    assert all(r.headers["x-test-key"] == "test-key" for r in requests)
    assert sleeps == [0.5, 0.5]


def test_blank_smiles_makes_no_request() -> None:
    lookup, requests = _lookup([])
    assert lookup.get_properties("  ") == {}
    assert requests == []


def test_no_match_returns_empty_and_is_cached() -> None:
    lookup, requests = _lookup([], dtxsid_body=[])
    assert lookup.get_properties("CCO") == {}
    assert lookup.get_properties("CCO") == {}
    assert len(requests) == 1


def test_404_is_cached() -> None:
    lookup, requests = _lookup([], dtxsid_status=404, dtxsid_body={"error": "x"})
    assert lookup.get_properties("CCO") == {}
    lookup.get_properties("CCO")
    assert len(requests) == 1


@pytest.mark.parametrize("env", [{}, {"TEST_KEY_VAR": "  "}])
def test_missing_api_key_raises_without_request(env: dict[str, str]) -> None:
    lookup, requests = _lookup([], env=env)
    with pytest.raises(RuntimeError, match="TEST_KEY_VAR"):
        lookup.get_properties("CCO")
    assert requests == []


def test_success_is_cached() -> None:
    lookup, requests = _lookup([_entry("Density", experimental=1.0)])
    first = lookup.get_properties("CCO")
    first.clear()
    assert "density" in lookup.get_properties("CCO")
    assert len(requests) == 2


def test_network_error_not_cached() -> None:
    lookup, requests = _lookup([], fail=httpx.ConnectError("down"))
    assert lookup.get_properties("CCO") == {}
    assert lookup.get_properties("CCO") == {}
    assert len(requests) == 2


@pytest.mark.parametrize(
    ("kwargs"),
    [
        {"dtxsid_status": 500},
        {"summary_status": 500},
        {"summary": "not json"},
        {"dtxsid_body": {"not": "a list"}},
        {"dtxsid_body": [{"no": "dtxsid"}]},
    ],
)
def test_failures_return_empty_and_are_not_cached(kwargs: dict[str, object]) -> None:
    args: dict[str, object] = {"summary": [], **kwargs}
    lookup, requests = _lookup(**args)  # pyright: ignore[reportArgumentType]
    assert lookup.get_properties("CCO") == {}
    count = len(requests)
    lookup.get_properties("CCO")
    assert len(requests) == 2 * count
