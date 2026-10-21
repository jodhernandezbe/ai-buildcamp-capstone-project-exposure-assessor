"""Tests for the app factory: origin guard, sanitised errors and the static frontend."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.main import create_app
from config.ui import UiSettings
from tests.api.conftest import ORIGIN

KEY = "sk-proj-" + "m3N4b5V6c7" * 3  # pragma: allowlist secret
BODY = {"api_key": "sk-" + "a" * 20}  # pragma: allowlist secret


def test_foreign_origin_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/settings/openai-key", json=BODY, headers={"Origin": "https://example.com"}
    )
    assert response.status_code == 403


def test_missing_origin_is_rejected_for_writes(client: TestClient) -> None:
    assert client.post("/api/v1/settings/openai-key", json=BODY).status_code == 403
    assert client.delete("/api/v1/settings/openai-key").status_code == 403


def test_referer_of_own_origin_is_accepted(client: TestClient) -> None:
    response = client.delete("/api/v1/settings/openai-key", headers={"Referer": ORIGIN + "/page"})
    assert response.status_code == 200


def test_own_origin_is_accepted(client: TestClient) -> None:
    response = client.post("/api/v1/settings/openai-key", json=BODY, headers={"Origin": ORIGIN})
    assert response.status_code == 200


def test_rebinding_host_is_rejected(app: FastAPI) -> None:
    with TestClient(app, base_url="http://evil.example:8000") as client:
        assert client.get("/api/v1/settings/openai-key").status_code == 403


def test_validation_errors_do_not_echo_values(client: TestClient) -> None:
    response = client.post(
        "/api/v1/settings/openai-key", json={"api_key": 5, "other": KEY}, headers={"Origin": ORIGIN}
    )
    assert response.status_code == 422
    assert KEY not in response.text
    assert {"loc", "msg"} == set(response.json()["fields"][0])


def test_unhandled_errors_are_generic_and_logged_redacted(
    app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    @app.get("/api/boom")
    def boom() -> None:
        raise RuntimeError(f"provider said {KEY}")

    with TestClient(app, base_url=ORIGIN, raise_server_exceptions=False) as client:
        response = client.get("/api/boom")
    body = response.json()
    assert response.status_code == 500
    assert set(body) == {"error", "correlation_id"}
    assert KEY not in response.text
    assert body["correlation_id"] in caplog.text


def test_frontend_is_served_when_built(settings: UiSettings, tmp_path: Path) -> None:
    dist = tmp_path / "built"
    dist.mkdir()
    (dist / "index.html").write_text("<html>shell</html>")
    app = create_app(replace(settings, frontend_dist=dist))
    with TestClient(app, base_url=ORIGIN) as client:
        assert "shell" in client.get("/").text
        assert client.get("/api/v1/settings/openai-key").status_code == 200
