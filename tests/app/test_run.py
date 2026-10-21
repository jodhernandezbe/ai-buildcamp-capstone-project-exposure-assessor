"""Tests for the command line run: it uses the stored keys, falling back to the environment."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, ToolCall
from langchain_core.tools import tool

from app.key_vault import default_service_keys
from app.run import ask, stored_keys_provided
from tests.fakes import (
    CENSUS_ENTRY,
    COMPTOX_ENTRY,
    OPENAI_ENTRY,
    FakeCredentialStore,
    ScriptedChatModel,
)
from tools.credentials import CENSUS_KEY, COMPTOX_KEY, PROVIDER_KEY

STORED: dict[tuple[str, str], str] = {
    OPENAI_ENTRY: "sk-stored-" + "o" * 20,  # pragma: allowlist secret
    CENSUS_ENTRY: "stored-census-" + "c" * 20,  # pragma: allowlist secret
    COMPTOX_ENTRY: "stored-comptox-" + "t" * 20,  # pragma: allowlist secret
}


@tool
def probe_all() -> str:
    """Report which keys this tool can see (test double for tools that need keys)."""
    seen = [holder.get() for holder in (PROVIDER_KEY, CENSUS_KEY, COMPTOX_KEY)]
    return ",".join(key.get_secret_value() if key else "none" for key in seen)


def _store(*entries: tuple[str, str]) -> FakeCredentialStore:
    store = FakeCredentialStore()
    store.entries.update({entry: STORED[entry] for entry in entries})
    return store


def test_every_stored_key_reaches_the_tools_during_the_run() -> None:
    keys = default_service_keys(_store(OPENAI_ENTRY, CENSUS_ENTRY, COMPTOX_ENTRY))
    with stored_keys_provided(keys):
        assert probe_all.invoke({}) == ",".join(STORED.values())
    assert probe_all.invoke({}) == "none,none,none"


def test_a_key_that_is_not_stored_is_left_to_its_environment_variable() -> None:
    keys = default_service_keys(_store(CENSUS_ENTRY))
    with stored_keys_provided(keys):
        assert probe_all.invoke({}) == f"none,{STORED[CENSUS_ENTRY]},none"


def test_an_unavailable_keychain_provides_nothing_and_does_not_fail() -> None:
    keys = default_service_keys(FakeCredentialStore(fail=True))
    with stored_keys_provided(keys):
        assert probe_all.invoke({}) == "none,none,none"


def test_ask_gives_the_agents_tools_the_stored_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agent.graph.get_all_tools", lambda: [probe_all])
    call = AIMessage(content="", tool_calls=[ToolCall(name="probe_all", args={}, id="c1")])
    model = ScriptedChatModel([call, AIMessage(content="final answer")])
    keys = default_service_keys(_store(OPENAI_ENTRY, CENSUS_ENTRY, COMPTOX_ENTRY))
    assert ask("Assess CAS 71-43-2", model, keys) == "final answer"
    assert CENSUS_KEY.get() is None  # nothing is left behind once the run is over
