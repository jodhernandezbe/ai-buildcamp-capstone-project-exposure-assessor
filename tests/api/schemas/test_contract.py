"""Tests for the wire contract: validation rules and the committed schema staying current."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from api.schemas.chat import ChatRequest, StreamEvent, Token, TurnFinished
from api.schemas.contract import contract_json
from api.schemas.settings import KeyUpdatePayload

SCHEMA = Path(__file__).resolve().parents[3] / "frontend" / "src" / "types" / "schema.json"
KEY = "sk-" + "Z" * 30  # pragma: allowlist secret


def test_committed_schema_is_current() -> None:
    assert SCHEMA.read_text(encoding="utf-8") == contract_json(), (
        "run: uv run python -m scripts.export_contract && npm --prefix frontend run gen:types"
    )


@pytest.mark.parametrize(
    "body",
    [
        {"thread_id": "t1", "message": ""},
        {"thread_id": "bad id!", "message": "hi"},
        {"thread_id": "t" * 65, "message": "hi"},
        {"thread_id": "t1", "message": "x" * 8001},
        {"thread_id": "t1", "message": "hi", "extra": 1},
    ],
)
def test_chat_request_rejects_bad_bodies(body: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(body)


def test_key_payload_never_shows_the_key() -> None:
    payload = KeyUpdatePayload.model_validate({"api_key": KEY})
    assert KEY not in repr(payload)
    assert KEY not in payload.model_dump_json()
    assert payload.api_key.get_secret_value() == KEY


def test_events_round_trip_through_the_union() -> None:
    adapter: TypeAdapter[StreamEvent] = TypeAdapter(StreamEvent)
    event = adapter.validate_json(Token(seq=3, text="hi").model_dump_json())
    assert isinstance(event, Token)
    assert TurnFinished(seq=1).model_dump() == {"seq": 1, "type": "turn_finished"}


def test_models_are_frozen() -> None:
    event = Token(seq=0, text="a")
    with pytest.raises(ValidationError):
        event.text = "b"  # type: ignore[misc]
