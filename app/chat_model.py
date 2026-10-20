"""Chat model factory: the only module that imports a chat provider package.

The program and the evaluations both build the agent's model here from ``[agent]`` in
``config/settings.toml``, so they always run the same model. A new provider is an entry in
``_PROVIDERS`` plus ``config.agent.SUPPORTED_CHAT_PROVIDERS``.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from config.agent import AgentSettings


def _openai_chat(model: str, api_key: str, timeout_seconds: float) -> BaseChatModel:
    from langchain_openai import ChatOpenAI  # provider package: imported only here

    return ChatOpenAI(model=model, api_key=SecretStr(api_key), timeout=timeout_seconds)


_PROVIDERS: Mapping[str, Callable[[str, str, float], BaseChatModel]] = {
    "openai": _openai_chat,
}


def build_named_chat_model(
    provider: str,
    model: str,
    api_key_env_var: str,
    timeout_seconds: float,
    environ: Mapping[str, str] | None = None,
) -> BaseChatModel:
    """Build ``model`` of ``provider``, reading its API key from ``api_key_env_var``.

    Raises:
        RuntimeError: If the API-key environment variable is unset or blank.
        ValueError: If the provider is not supported (a configuration error).
    """
    env = os.environ if environ is None else environ
    api_key = env.get(api_key_env_var, "").strip()
    if not api_key:
        raise RuntimeError(f"{api_key_env_var} is not set")
    build = _PROVIDERS.get(provider)
    if build is None:
        raise ValueError(f"unsupported chat provider: {provider}")
    return build(model, api_key, timeout_seconds)


def build_chat_model(
    settings: AgentSettings, environ: Mapping[str, str] | None = None
) -> BaseChatModel:
    """Build the agent's chat model from the ``[agent]`` settings (the outer edge).

    Args:
        settings: Provider, model, API-key variable name and timeout (seconds).
        environ: Environment the API key is read from; defaults to ``os.environ``.

    Raises:
        RuntimeError: If the API-key environment variable is unset or blank.
        ValueError: If the provider is not supported.
    """
    return build_named_chat_model(
        settings.provider,
        settings.model,
        settings.api_key_env_var,
        settings.timeout_seconds,
        environ,
    )
