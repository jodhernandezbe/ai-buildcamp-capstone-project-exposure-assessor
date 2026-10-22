"""Chemical property lookup tool."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.tools import tool

from commons.cas import format_cas
from commons.units import UnitConversionError, convert
from config.loader import (
    ComptoxSettings,
    MolecularWeightSpec,
    ToxicityValueSpec,
    get_comptox_settings,
    get_unit_settings,
)
from tools.informatics.helpers.comptox import ComptoxLookup
from tools.schemas import ChemicalProperties, PropertyValue, ToxicityDetail, ToxicityValue

# Output fields filled from CompTox; keys must match the configured result keys.
_PROPERTY_FIELDS = ("vapor_pressure", "density")
_TOXICITY_FIELDS = ("rfd", "rfc", "sf", "iur")
_NO_COMPTOX_DATA = "no CompTox data retrieved (not found or service unavailable)"
_UNRESOLVED = (
    "CAS number {cas!r} could not be resolved in CompTox (not found or service unavailable)"
)
_NO_NAME = "preferred_name: CompTox gave no name; refer to the chemical by its CAS number"


def _positive(value: float) -> bool:
    return math.isfinite(value) and value > 0


@dataclass
class _Collected:
    """Values, provenance and warnings gathered while building one result."""

    values: dict[str, float | None]
    sources: dict[str, str]
    details: dict[str, ToxicityDetail]
    warnings: list[str]
    name: str | None = None

    @classmethod
    def empty(cls) -> _Collected:
        fields = ("molecular_weight", *_PROPERTY_FIELDS, *_TOXICITY_FIELDS)
        return cls(dict.fromkeys(fields), {}, {}, [])

    def add_name(self, name: str | None) -> None:
        """The name CompTox gave, with its source; else a warning (never a name from elsewhere)."""
        self.name = name
        if name is None:
            self.warnings.append(_NO_NAME)
        else:
            self.sources["preferred_name"] = "CompTox"

    def to_properties(self) -> ChemicalProperties:
        v = self.values
        return {
            "preferred_name": self.name,
            "molecular_weight": v["molecular_weight"],
            "vapor_pressure": v["vapor_pressure"],
            "density": v["density"],
            "rfd": v["rfd"],
            "rfc": v["rfc"],
            "sf": v["sf"],
            "iur": v["iur"],
            "sources": self.sources,
            "toxicity_details": self.details,
            "warnings": self.warnings,
        }


def _convert_checked(
    out: _Collected,
    field: str,
    value: float,
    unit: str,
    target: str,
    aliases: dict[str, str],
) -> float | None:
    """Convert ``value`` to ``target``; None (with a warning) if it fails or is not positive."""
    try:
        converted = convert(value, unit, target, aliases)
    except UnitConversionError as exc:
        out.warnings.append(f"{field}: {exc}")
        return None
    if not _positive(converted):
        out.warnings.append(
            f"{field}: rejected value {converted!r} {target} (must be a finite number "
            "greater than zero)"
        )
        return None
    return converted


Reported = tuple[float, str, str]  # (value, unit as reported, source)


def _reported(record: PropertyValue | ToxicityValue | None) -> Reported | None:
    return (record["value"], record["unit"], record["source"]) if record else None


def _add_one(
    out: _Collected,
    field: str,
    reported: Reported | None,
    target: str | None,
    aliases: dict[str, str],
) -> bool:
    """Add one converted value to ``out``; return whether it was added."""
    if target is None:
        out.warnings.append(f"{field}: not configured")
    elif reported is None:
        out.warnings.append(f"{field}: not found in CompTox")
    else:
        value, unit, source = reported
        converted = _convert_checked(out, field, value, unit, target, aliases)
        if converted is not None:
            out.values[field] = converted
            out.sources[field] = source
            return True
    return False


def _add_molecular_weight(
    out: _Collected,
    weight: float | None,
    spec: MolecularWeightSpec,
    aliases: dict[str, str],
) -> None:
    reported = (weight, spec.unit, "CompTox") if weight is not None else None
    _add_one(out, "molecular_weight", reported, spec.target_unit, aliases)


def _add_toxicity(
    out: _Collected,
    field: str,
    record: ToxicityValue | None,
    spec: ToxicityValueSpec | None,
    aliases: dict[str, str],
) -> None:
    target = spec.target_unit if spec else None
    if _add_one(out, field, _reported(record), target, aliases) and record and spec:
        out.details[field] = {
            "source": record["source"],
            "exposure_route": spec.applied_route,
            "route_reported": record["route"],
            "endpoint": record["endpoint"],
            "assessment": record["assessment"],
        }


def _add_comptox_values(
    out: _Collected,
    found: dict[str, PropertyValue],
    toxicity: dict[str, ToxicityValue],
    settings: ComptoxSettings,
    aliases: dict[str, str],
) -> None:
    if not found and not toxicity:
        out.warnings.append(_NO_COMPTOX_DATA)
        return
    targets = {spec.key: spec.target_unit for spec in settings.properties}
    specs = {spec.key: spec for spec in settings.toxicity_values}
    for field in _PROPERTY_FIELDS:
        _add_one(out, field, _reported(found.get(field)), targets.get(field), aliases)
    for field in _TOXICITY_FIELDS:
        _add_toxicity(out, field, toxicity.get(field), specs.get(field), aliases)


def lookup_chemical_properties(
    cas_number: str,
    comptox: ComptoxLookup,
    settings: ComptoxSettings,
    aliases: dict[str, str],
) -> ChemicalProperties:
    """Collect a chemical's properties from CompTox in the configured target units.

    Every value is checked before it is returned: it must convert to the target unit and be
    a finite number greater than zero; otherwise the field is None with a warning.

    Args:
        cas_number: CAS registry number, e.g. "71-43-2".
        comptox: CompTox molecular weight, property and toxicity lookup.
        settings: CompTox settings; supplies each field's target unit.
        aliases: Unit-spelling aliases passed to the converter.

    Returns:
        Every field of ``ChemicalProperties``; None where unavailable, with a warning.

    Raises:
        RuntimeError: If the CAS number is valid and the CompTox API key environment
            variable is not set.
    """
    out = _Collected.empty()
    cas = format_cas(cas_number)
    if cas is None:
        out.warnings.append(f"CAS number {cas_number!r} is not valid and could not be resolved")
        return out.to_properties()
    weight = comptox.get_molecular_weight(cas)
    found = comptox.get_properties(cas)
    toxicity = comptox.get_toxicity_values(cas)
    if weight is None and not found and not toxicity:
        out.warnings.append(_UNRESOLVED.format(cas=cas))
        return out.to_properties()
    out.add_name(comptox.get_preferred_name(cas))
    _add_molecular_weight(out, weight, settings.molecular_weight, aliases)
    _add_comptox_values(out, found, toxicity, settings, aliases)
    return out.to_properties()


@dataclass(frozen=True)
class _Services:
    comptox: ComptoxLookup
    settings: ComptoxSettings
    aliases: dict[str, str]


@lru_cache(maxsize=1)
def _services() -> _Services:
    """Build the default collaborators once so the HTTP client and caches are shared."""
    return _Services(
        comptox=ComptoxLookup(),
        settings=get_comptox_settings(),
        aliases=get_unit_settings().aliases,
    )


@tool
def fetch_chemical_properties(cas_number: str) -> ChemicalProperties:
    """Fetch physical-chemical properties and toxicity values for a chemical.

    Purpose:
        Use this to learn what a chemical is and how hazardous it is to breathe or ingest:
        its toxicity benchmarks (`rfc`, `iur`) are what an exposure result is judged
        against, so without them a concentration can be computed but not interpreted. A
        benchmark that comes back null means no usable value exists in the source; the
        matching risk cannot be computed and that must be reported, not replaced by a
        guess. Every value is converted to the fixed unit listed below, so results can be
        used directly (pass `rfc` and `iur` to `calculate_exposure_metrics` as they are).
        `preferred_name` is the only name to call the chemical by; when it is null, refer
        to the chemical by its CAS number alone and never supply a name for it.

    Args:
        cas_number: CAS registry number as the user gave it, e.g. "71-43-2" for benzene
            (hyphens optional). Never a number recalled from a chemical's name: if the user
            gave only a name, ask for the CAS number instead of calling this tool.

    Returns:
        A dict with:
        - preferred_name: the name CompTox calls the chemical by (null when CompTox gave
          none: then the chemical is referred to by its CAS number only)
        - molecular_weight: g/mol (average mass)
        - vapor_pressure: mmHg, as reported by the source (typically at 25 C)
        - density: g/cm^3
        - rfd: oral reference dose, mg/(kg*day) (non-cancer benchmark for ingestion)
        - rfc: inhalation reference concentration, mg/m^3 (non-cancer benchmark)
        - sf: oral cancer slope factor, (mg/(kg*day))^-1
        - iur: inhalation unit risk, (ug/m^3)^-1 (cancer potency)
        - sources: for each value found, "CompTox" (name and molecular weight),
          "experimental" or "predicted" (properties), or the toxicity database name
        - toxicity_details: for each of rfd, rfc, sf and iur that has a value:
          source (database), exposure_route (the route the value applies to: "oral" for
          rfd and sf, "inhalation" for rfc and iur), route_reported (the route as the
          source recorded it, "not specified" if it gave none), endpoint (the critical
          effect or cancer endpoint, e.g. "leukemia"; null if the source gave none) and
          assessment ("cancer" or "non-cancer")
        - warnings: one message per value that is None

        When you report a toxicity value, say which exposure route it applies to, its
        source and its endpoint from `toxicity_details`.

        Toxicity values come from the highest-priority database that has them (IRIS
        first). When that database lists several values, the most conservative is
        returned: the lowest RfD or RfC, the highest slope factor or unit risk.

        Any value is None when it was not found, its reported unit could not be
        converted safely, or it was not a positive number; check `warnings` and tell
        the user rather than guessing.
    """
    services = _services()
    return lookup_chemical_properties(
        cas_number,
        services.comptox,
        services.settings,
        services.aliases,
    )
