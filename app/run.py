"""Run the agent on one question with the configured model and step limit."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from agent.graph import build_agent
from app.chat_model import build_chat_model
from config.agent import AgentSettings, get_agent_settings


def run_config(settings: AgentSettings) -> RunnableConfig:
    """LangGraph run configuration from the ``[agent]`` settings (the step limit)."""
    return {"recursion_limit": settings.recursion_limit}


def ask(question: str, model: BaseChatModel | None = None) -> str:
    """Return the agent's final answer to ``question``.

    Args:
        question: The user's request.
        model: Chat model to use; defaults to the one configured in ``[agent]``.
    """
    settings = get_agent_settings()
    agent = build_agent(model if model is not None else build_chat_model(settings))
    result = agent.invoke({"messages": [HumanMessage(content=question)]}, run_config(settings))
    last = result["messages"][-1]
    return last.text if isinstance(last, AIMessage) else str(last.content)
