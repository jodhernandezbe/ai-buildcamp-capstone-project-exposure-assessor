"""FastAPI ``Depends()`` providers; tests override them with fakes."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from agent.graph import DEFAULT_SYSTEM_PROMPT
from agent.guardrails import ScopeGuard
from api.core.config import ui_settings
from api.core.security_keyring import default_service_keys
from api.services.agent_runner import AgentRuntime
from api.services.projectors.rules import WorkspaceRules
from api.services.threads import ThreadStore
from app.chat_model import build_chat_model
from app.key_vault import ServiceKeys
from config.agent import get_agent_settings
from config.population import get_population_settings
from config.ui import UiSettings
from prompts.registry import load_prompt


def get_settings() -> UiSettings:
    """The UI settings."""
    return ui_settings()


def get_service_keys() -> ServiceKeys:
    """The OS-keychain vaults of every key; keys are read from them once per turn, never cached."""
    return default_service_keys()


def _scope_guard(ui: UiSettings) -> ScopeGuard:
    names = ui.prompts
    return ScopeGuard(
        classifier_prompt=load_prompt(names.classifier),
        fallback_reply=load_prompt(names.fallback),
        history_window=names.history_window,
    )


def _workspace_rules(ui: UiSettings) -> WorkspaceRules:
    return WorkspaceRules(
        thresholds=ui.thresholds,
        coordinate_tolerance_deg=ui.map.coordinate_tolerance_deg,
        default_radius_km=get_population_settings().default_radius_km,
        sector_half_angle_deg=ui.map.sector_half_angle_deg,
        vertex_spacing_deg=ui.map.vertex_spacing_deg,
    )


def get_runtime() -> AgentRuntime:
    """The configured chat model factory, step limit, labels, prices, guard, prompt and rules."""
    settings = get_agent_settings()
    ui = ui_settings()
    return AgentRuntime(
        build_model=lambda key: build_chat_model(settings, api_key=key),
        recursion_limit=settings.recursion_limit,
        step_labels=ui.step_labels,
        model_name=settings.model,
        pricing=ui.pricing,
        scope_guard=_scope_guard(ui),
        system_prompt=f"{load_prompt(DEFAULT_SYSTEM_PROMPT)}\n\n{load_prompt(ui.prompts.addendum)}",
        workspace_rules=_workspace_rules(ui),
    )


def get_threads(request: Request) -> ThreadStore:
    """The in-memory thread store of this app."""
    return cast(ThreadStore, request.app.state.threads)
