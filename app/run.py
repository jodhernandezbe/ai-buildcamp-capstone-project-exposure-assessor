"""Run the agent on one question with the configured model and step limit."""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import ExitStack, contextmanager

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from agent.completion import CompletionGuard
from agent.graph import build_agent
from app.chat_model import build_chat_model
from app.key_vault import KeyringVault, ServiceKeys, default_service_keys, stored_key
from config.agent import AgentSettings, get_agent_settings
from config.ui import KEY_NAMES, get_ui_settings
from prompts.registry import load_prompt
from tools.credentials import HOLDERS


def completion_guard() -> CompletionGuard | None:
    """The completion check the web program also uses, from ``[ui.prompts]``; None when off."""
    names = get_ui_settings().prompts
    if names.max_nudges == 0:
        return None
    return CompletionGuard(
        classifier_prompt=load_prompt(names.completion),
        nudge=load_prompt(names.nudge),
        max_nudges=names.max_nudges,
    )


def run_config(settings: AgentSettings) -> RunnableConfig:
    """LangGraph run configuration from the ``[agent]`` settings (the step limit)."""
    return {"recursion_limit": settings.recursion_limit}


def program_model(
    settings: AgentSettings,
    vault: KeyringVault | None = None,
    environ: Mapping[str, str] | None = None,
) -> BaseChatModel:
    """Build the program's chat model with the key stored in the OS keychain.

    Falls back to the ``[agent]`` API-key environment variable when the keychain holds no key
    or is unavailable (headless runs such as CI).

    Raises:
        RuntimeError: If neither the keychain nor the environment variable has a key.
    """
    chosen = vault if vault is not None else default_service_keys().vault("openai")
    return build_chat_model(settings, environ, api_key=stored_key(chosen))


@contextmanager
def stored_keys_provided(keys: ServiceKeys) -> Generator[None]:
    """Give the tools the keys stored in the keychain while a run lasts (the CLI's counterpart
    of the web program's per-turn keys); a key that is not stored falls back to its variable."""
    with ExitStack() as stack:
        for name in KEY_NAMES:
            key = stored_key(keys.vault(name))
            if key is not None:
                stack.enter_context(HOLDERS[name].provide(key))
        yield


def ask(question: str, model: BaseChatModel | None = None, keys: ServiceKeys | None = None) -> str:
    """Return the agent's final answer to ``question``.

    Args:
        question: The user's request.
        model: Chat model to use; defaults to the one configured in ``[agent]``.
        keys: Key vaults to read; defaults to the OS keychain ones named in ``[ui.keyring]``.
    """
    settings = get_agent_settings()
    vaults = keys if keys is not None else default_service_keys()
    agent = build_agent(
        model if model is not None else program_model(settings, vaults.vault("openai")),
        completion_guard=completion_guard(),
    )
    with stored_keys_provided(vaults):
        result = agent.invoke({"messages": [HumanMessage(content=question)]}, run_config(settings))
    last = result["messages"][-1]
    return last.text if isinstance(last, AIMessage) else str(last.content)
