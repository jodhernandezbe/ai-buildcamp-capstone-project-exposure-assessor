"""Tests that the agent accepts an injected chat model."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from agent.graph import build_agent


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> FakeToolModel:
        return self


def test_build_agent_with_injected_model() -> None:
    model = FakeToolModel(messages=iter([AIMessage(content="done")]))
    agent = build_agent(model)
    result = agent.invoke({"messages": [HumanMessage(content="hi")]})
    assert result["messages"][-1].content == "done"
