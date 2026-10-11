"""LangGraph agent scaffold.

The chat model is an injected dependency: this module only knows about
``BaseChatModel`` and never imports a provider package (OpenAI, Anthropic, ...).
"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState
from prompts.registry import load_prompt
from tools.registry import get_all_tools

DEFAULT_SYSTEM_PROMPT = "agent_system"


def build_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool] | None = None,
    system_prompt: str | None = None,
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    """Compile a tool-calling agent graph around an injected chat model.

    Args:
        model: Any LangChain chat model that supports tool calling. Constructed
            by the caller so the provider can be swapped without touching this module.
        tools: Tools to bind. Defaults to everything in the tool registry.
        system_prompt: System prompt text. Defaults to ``prompts/agent_system.md``.

    Returns:
        A compiled graph; invoke it with ``{"messages": [...]}``.
    """
    bound_tools = list(tools) if tools is not None else get_all_tools()
    prompt_text = system_prompt if system_prompt is not None else load_prompt(DEFAULT_SYSTEM_PROMPT)
    runnable = model.bind_tools(bound_tools) if bound_tools else model

    def call_model(state: AgentState) -> AgentState:
        messages = [SystemMessage(content=prompt_text), *state["messages"]]
        return {"messages": [runnable.invoke(messages)]}

    graph = StateGraph(AgentState)
    graph.add_node("model", call_model)
    graph.add_edge(START, "model")
    if bound_tools:
        graph.add_node("tools", ToolNode(bound_tools))
        graph.add_conditional_edges("model", tools_condition)
        graph.add_edge("tools", "model")
    else:
        graph.add_edge("model", END)
    return graph.compile()
