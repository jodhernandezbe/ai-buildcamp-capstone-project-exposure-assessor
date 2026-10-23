"""Builders for PUG View records of the real shape, with obviously synthetic values."""

from __future__ import annotations

from collections.abc import Sequence

Json = dict[str, object]


def info(text: str, unit: str | None = None) -> Json:
    """One information entry holding a single string (and, optionally, a separate unit)."""
    value: Json = {"StringWithMarkup": [{"String": text}]}
    if unit is not None:
        value["Unit"] = unit
    return {"ReferenceNumber": 1, "Value": value}


def section(heading: object, *children: Json, entries: Sequence[Json] = ()) -> Json:
    """A section with child sections and information entries."""
    body: Json = {"TOCHeading": heading}
    if children:
        body["Section"] = list(children)
    if entries:
        body["Information"] = list(entries)
    return body


def record(
    *,
    cas: Sequence[str] = (),
    weight: Sequence[Json] = (),
    pressure: Sequence[Json] = (),
    density: Sequence[Json] = (),
) -> Json:
    """A record with the sections the client reads; empty sequences leave a section out."""
    identifiers = section(
        "Names and Identifiers",
        section(
            "Other Identifiers",
            section("CAS", entries=[info(c) for c in cas]) if cas else {"TOCHeading": "Other"},
        ),
    )
    computed = section("Computed Properties", section("Molecular Weight", entries=weight))
    experimental = section(
        "Experimental Properties",
        section("Vapor Pressure", entries=pressure),
        section("Density", entries=density),
    )
    properties = section(
        "Chemical and Physical Properties",
        *([computed] if weight else []),
        *([experimental] if pressure or density else []),
    )
    return {"Record": {"RecordType": "CID", "Section": [identifiers, properties]}}
