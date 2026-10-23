"""Typed loader for the ``[comptox.iris]`` settings (CompTox's IRIS endpoint)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from config.parsing import as_table, names, require_number, require_str

_NAME = "comptox.iris"


@dataclass(frozen=True)
class IrisFieldSpec:
    """One toxicity value read from the IRIS endpoint.

    Attributes:
        key: Toxicity value it fills, e.g. ``"rfc"`` (a ``[[comptox.toxicity_values]]`` key).
        field: Field of the endpoint's record holding its text, e.g. ``"rfcChronic"``.
        units: Unit spellings accepted after the number, exactly as the endpoint writes them.
    """

    key: str
    field: str
    units: tuple[str, ...]


@dataclass(frozen=True)
class IrisSettings:
    """The IRIS endpoint, the fields read from it and how its values are reported.

    Attributes:
        path: Path template appended to the CompTox base URL; contains ``{dtxsid}``.
        source: ``source`` reported for a value that comes from the endpoint.
        source_revised: The same with the revision date; contains ``{revision}``.
        toxval_source: ToxVal ``source`` of IRIS records, to compare the endpoint's value with.
        effects_field: Field holding the critical-effect systems (one per line).
        revision_field: Field holding the date of the last significant revision.
        agreement_tolerance: Largest relative difference from the ToxVal IRIS value that goes
            without a warning.
        fields: The values read, in order.
    """

    path: str
    source: str
    source_revised: str
    toxval_source: str
    effects_field: str
    revision_field: str
    agreement_tolerance: float
    fields: tuple[IrisFieldSpec, ...]


def _template(table: dict[str, object], key: str, slot: str) -> str:
    value = require_str(table, key, _NAME)
    if f"{{{slot}}}" not in value:
        raise ValueError(f"{_NAME}.{key} must contain {{{slot}}}")
    return value


def _field(raw: object, index: int) -> IrisFieldSpec:
    name = f"{_NAME}.fields[{index}]"
    table = as_table(raw, name)
    return IrisFieldSpec(
        key=require_str(table, "key", name),
        field=require_str(table, "field", name),
        units=names(table, "units", name, allow_empty=False),
    )


def _fields(table: dict[str, object], toxicity_keys: tuple[str, ...]) -> tuple[IrisFieldSpec, ...]:
    raw = table.get("fields")
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{_NAME}.fields must be a non-empty list of tables")
    fields = tuple(_field(item, i) for i, item in enumerate(cast(list[object], raw)))
    if len({spec.key for spec in fields}) != len(fields):
        raise ValueError(f"{_NAME}.fields has a key listed twice")
    for spec in fields:
        if spec.key not in toxicity_keys:
            raise ValueError(f"{_NAME}.fields: {spec.key!r} is not a comptox.toxicity_values key")
    return fields


def parse_iris(comptox: dict[str, object], toxicity_keys: tuple[str, ...]) -> IrisSettings | None:
    """Parse and validate ``[comptox.iris]`` of the ``comptox`` table; None if it is absent.

    Raises:
        ValueError: If a key is missing or invalid; the message names the key.
    """
    if "iris" not in comptox:
        return None
    table = as_table(comptox["iris"], _NAME)
    return IrisSettings(
        path=_template(table, "path", "dtxsid"),
        source=require_str(table, "source", _NAME),
        source_revised=_template(table, "source_revised", "revision"),
        toxval_source=require_str(table, "toxval_source", _NAME),
        effects_field=require_str(table, "effects_field", _NAME),
        revision_field=require_str(table, "revision_field", _NAME),
        agreement_tolerance=require_number(table, "agreement_tolerance", minimum=0, name=_NAME),
        fields=_fields(table, toxicity_keys),
    )
