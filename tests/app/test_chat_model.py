"""Tests for the chat model factory and the program run."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.chat_model import build_chat_model, build_named_chat_model
from app.run import ask, run_config
from config.agent import AgentSettings, get_agent_settings

SETTINGS = AgentSettings(
    provider="openai",
    model="chat-test",
    api_key_env_var="TEST_KEY_VAR",  # pragma: allowlist secret
    timeout_seconds=5.0,
    recursion_limit=7,
)
ENV = {"TEST_KEY_VAR": "not-a-real-key"}  # pragma: allowlist secret


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> FakeToolModel:
        return self


def test_builds_the_configured_model() -> None:
    model = build_chat_model(SETTINGS, ENV)
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "chat-test"


def test_shipped_settings_build_their_model() -> None:
    settings = get_agent_settings()
    model = build_chat_model(settings, {settings.api_key_env_var: "not-a-real-key"})
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == settings.model


@pytest.mark.parametrize("env", [{}, {"TEST_KEY_VAR": "  "}])
def test_missing_key_raises(env: dict[str, str]) -> None:
    with pytest.raises(RuntimeError, match="TEST_KEY_VAR is not set"):
        build_chat_model(SETTINGS, env)


def test_unsupported_provider_raises() -> None:
    with pytest.raises(ValueError, match="unsupported chat provider: other"):
        build_named_chat_model("other", "m", "TEST_KEY_VAR", 5.0, ENV)


def test_run_config_carries_the_step_limit() -> None:
    assert run_config(SETTINGS) == {"recursion_limit": 7}


def test_ask_returns_the_final_answer_of_an_injected_model() -> None:
    model = FakeToolModel(messages=iter([AIMessage(content="final answer")]))
    assert ask("Assess CAS 71-43-2", model) == "final answer"
