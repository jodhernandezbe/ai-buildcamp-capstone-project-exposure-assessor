"""Typed loader for ``[ui.exposure_graph]``: fixed text and units of the exposure chain graph.

Every value in the graph comes from a tool result; this table only names, labels and gives units.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from config.parsing import as_table, require_str, subtable

_NAME = "ui.exposure_graph"
LANES = ("community", "worker")
NODES = (
    "stack",
    "stack_release",
    "outdoor_air",
    "outdoor_inhalation",
    "age_band",
    "residents",
    "community_endpoint",
    "fugitive_release",
    "indoor_air",
    "worker_inhalation",
    "shift_worker",
    "worker_endpoint",
)
FACTS = (
    "chemical",
    "cas_number",
    "location",
    "industry",
    "condition_of_use",
    "life_cycle_stage",
    "stack_tier",
    "process",
    "stability_class",
    "weather_source",
    "population_source",
    "ventilation",
    "benchmark",
    "schedule_source",
    "assumptions",
    "tier",
)
QUANTITIES = (
    "total_release",
    "emission_rate",
    "operating_hours",
    "stack_height",
    "stack_diameter",
    "exit_velocity",
    "exit_temperature",
    "stack_peak",
    "peak_distance",
    "peak_concentration",
    "wind_speed",
    "residents",
    "radius",
    "band_share",
    "band_dose",
    "hq",
    "cancer_risk",
    "fugitive_release",
    "ventilation_rate",
    "mixing_factor",
    "workplace_concentration",
    "twa",
    "oel",
    "oel_ratio",
    "operating_days",
    "hours_per_day",
    "vapor_pressure",
)
TIERS = ("acceptable", "elevated", "exceedance")
VARIANTS = ("worst_case", "baseline")
REASONS = ("community", "worker", "missing")
_PLACEHOLDERS = {"stack": "{number}", "age_band": "{band}"}


@dataclass(frozen=True)
class QuantityText:
    """The label of a quantity and its unit; an empty unit means unitless."""

    label: str
    unit: str


@dataclass(frozen=True)
class GraphText:
    """Fixed text of the exposure graph, each table keyed by the names above (read-only maps).

    Attributes:
        source: Title of the source-facility node.
        lanes: Lane id -> lane label.
        nodes: Node key -> title (``stack`` has ``{number}``, ``age_band`` has ``{band}``).
        facts: Fact key -> label of a text value (a source, a class, a list).
        quantities: Quantity key -> label and unit.
        tiers: Worker risk tier -> its word.
        variants: Ventilation tier -> words appended to the worker quantities.
        reasons: Why a lane is unavailable (by lane id) or a value is absent (``missing``).
    """

    source: str
    lanes: Mapping[str, str]
    nodes: Mapping[str, str]
    facts: Mapping[str, str]
    quantities: Mapping[str, QuantityText]
    tiers: Mapping[str, str]
    variants: Mapping[str, str]
    reasons: Mapping[str, str]


def _text(table: dict[str, object], key: str, name: str) -> str:
    return require_str(table, key, name).strip()


def _unit(entry: dict[str, object], name: str) -> str:
    unit = entry.get("unit")
    if not isinstance(unit, str):
        raise ValueError(f"{name}.unit must be a string (empty for unitless)")
    return unit.strip()


def _strings(table: dict[str, object], key: str, keys: tuple[str, ...]) -> Mapping[str, str]:
    name = f"{_NAME}.{key}"
    sub = subtable(table, key, _NAME)
    return MappingProxyType({k: _text(sub, k, name) for k in keys})


def _nodes(table: dict[str, object]) -> Mapping[str, str]:
    nodes = _strings(table, "nodes", NODES)
    for key, placeholder in _PLACEHOLDERS.items():
        if nodes[key].count(placeholder) != 1:
            raise ValueError(f"{_NAME}.nodes.{key} must contain {placeholder} once")
    return nodes


def _quantity(sub: dict[str, object], key: str) -> QuantityText:
    name = f"{_NAME}.quantities.{key}"
    entry = as_table(sub.get(key), name)
    return QuantityText(label=_text(entry, "label", name), unit=_unit(entry, name))


def _quantities(table: dict[str, object]) -> Mapping[str, QuantityText]:
    sub = subtable(table, "quantities", _NAME)
    return MappingProxyType({key: _quantity(sub, key) for key in QUANTITIES})


def parse_exposure_graph(ui_table: dict[str, object]) -> GraphText:
    """Validate the ``exposure_graph`` table of an already-read ``[ui]`` table.

    Raises:
        ValueError: If a key is missing, empty or lacks its placeholder; the message names it.
    """
    table = subtable(ui_table, "exposure_graph", "ui")
    return GraphText(
        source=_text(table, "source", _NAME),
        lanes=_strings(table, "lanes", LANES),
        nodes=_nodes(table),
        facts=_strings(table, "facts", FACTS),
        quantities=_quantities(table),
        tiers=_strings(table, "tiers", TIERS),
        variants=_strings(table, "variants", VARIANTS),
        reasons=_strings(table, "reasons", REASONS),
    )
