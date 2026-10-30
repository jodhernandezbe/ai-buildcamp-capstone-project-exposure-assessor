"""Settings contract: the API-key vault and the display settings sent to the frontend."""

from __future__ import annotations

from pydantic import Field, SecretStr

from api.schemas.base import ContractModel


class KeyUpdatePayload(ContractModel):
    """Body of ``POST /api/v1/settings/openai-key``; the key is never echoed or logged."""

    api_key: SecretStr = Field(description="OpenAI API key to store in the OS keychain.")


class KeyStatusResponse(ContractModel):
    """Whether a key is stored; never the key or any part of it."""

    configured: bool


class KeysStatusResponse(ContractModel):
    """The status of every key the interface stores, in one response."""

    openai: KeyStatusResponse
    census: KeyStatusResponse
    comptox: KeyStatusResponse


class Thresholds(ContractModel):
    """Status thresholds (unitless HQ and lifetime cancer risk)."""

    hq_concern: float
    hq_near_lower: float
    cancer_lower: float
    cancer_upper: float


class WorkerThresholds(ContractModel):
    """Tier boundaries of the worker screening: above `*_exceedance` is "exceedance", above
    `*_elevated` is "elevated" (unitless; cancer risk is a probability)."""

    ratio_exceedance: float
    ratio_elevated: float
    hq_exceedance: float
    hq_elevated: float
    cancer_exceedance: float
    cancer_elevated: float


class InitialView(ContractModel):
    """A box on the map, decimal degrees (WGS84, west negative)."""

    west: float
    south: float
    east: float
    north: float


class MapConfig(ContractModel):
    """Basemap style URLs and the marker radii (px) for the smallest and largest emission rate."""

    light_style: str
    dark_style: str
    marker_min_px: float
    marker_max_px: float
    initial_view: InitialView = Field(description="What the map shows before any facility.")


class RailLayout(ContractModel):
    """Navigation rail widths in px: collapsed to icons, and the expanded default and limits."""

    collapsed_px: int
    default_px: int
    min_px: int
    max_px: int


class ChatLayout(ContractModel):
    """Chat dock: default and maximum shares of the viewport width (0-1), minimum width in px."""

    default_share: float
    min_px: int
    max_share: float


class OverviewLayout(ContractModel):
    """Overview panel height as shares (0-1) of the analysis area."""

    default_share: float
    min_share: float
    max_share: float


class LayoutConfig(ContractModel):
    """Workspace layout limits from the configuration."""

    rail: RailLayout
    chat: ChatLayout
    overview: OverviewLayout


class ClientConfig(ContractModel):
    """Display settings the frontend needs (``GET /api/v1/settings/client``)."""

    model: str = Field(description="Chat model that drives the agent.")
    thresholds: Thresholds
    worker_thresholds: WorkerThresholds
    map: MapConfig
    significant_digits: int
    narrow_breakpoint_px: int
    layout: LayoutConfig
    suggestions: list[str]
