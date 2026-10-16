"""Live smoke tests for fetch_chemical_properties with well-known substances.

Run with ``uv run pytest -m smoke`` (needs network access and COMPTOX_API_KEY in ``.env``).
Expected ranges come from widely published values for each substance (IRIS toxicity values,
handbook vapor pressure and density at about 25 C) and are deliberately wide: they catch a
wrong chemical, a wrong unit or a missing value, not small data revisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from typing import cast

import pytest

from tools.informatics.properties import fetch_chemical_properties
from tools.schemas import ChemicalProperties

pytestmark = [pytest.mark.smoke, pytest.mark.comptox]

Range = tuple[float, float]
# Target units of the tool: mg/(kg*day), mg/m^3, (mg/(kg*day))^-1, (ug/m^3)^-1.
UNITS = "mmHg, g/cm^3, mg/(kg*day), mg/m^3, (mg/(kg*day))^-1, (ug/m^3)^-1"


@dataclass(frozen=True)
class Expected:
    name: str
    cas: str
    molecular_weight: float  # g/mol
    ranges: dict[str, Range] = field(default_factory=dict[str, Range])
    absent: tuple[str, ...] = ()  # fields not expected to exist for this substance


SUBSTANCES = [
    Expected(
        "benzene",
        "71-43-2",
        78.11,
        {
            "vapor_pressure": (50.0, 150.0),
            "density": (0.8, 0.95),
            "rfd": (0.003, 0.005),
            "rfc": (0.02, 0.04),
            "sf": (0.015, 0.055),
            "iur": (2.2e-6, 7.8e-6),
        },
    ),
    Expected(
        "toluene",
        "108-88-3",
        92.14,
        {
            "vapor_pressure": (20.0, 50.0),
            "density": (0.8, 0.92),
            "rfd": (0.05, 0.1),
            "rfc": (3.0, 7.0),
        },
        absent=("sf", "iur"),  # not classifiable as to carcinogenicity
    ),
    Expected(
        "formaldehyde",
        "50-00-0",
        30.03,
        {"rfd": (0.1, 0.3), "iur": (1e-6, 1e-4)},
    ),
    Expected(
        "carbon tetrachloride",
        "56-23-5",
        153.82,
        {
            "vapor_pressure": (80.0, 150.0),
            "density": (1.5, 1.7),
            "rfd": (0.002, 0.008),
            "sf": (0.01, 0.2),
            "iur": (1e-6, 1e-4),
        },
    ),
]


@cache
def _fetch(cas: str) -> ChemicalProperties:
    return fetch_chemical_properties.invoke({"cas_number": cas})


def _value(result: ChemicalProperties, field_name: str) -> float | None:
    raw = cast(dict[str, object], result)[field_name]
    return raw if isinstance(raw, float) else None


@pytest.mark.parametrize("sub", SUBSTANCES, ids=lambda s: s.name)
def test_molecular_weight(sub: Expected) -> None:
    assert _fetch(sub.cas)["molecular_weight"] == pytest.approx(sub.molecular_weight, abs=0.05)


@pytest.mark.parametrize(
    ("sub", "name"),
    [(s, n) for s in SUBSTANCES for n in s.ranges],
    ids=lambda v: v if isinstance(v, str) else v.name,
)
def test_value_in_expected_range(sub: Expected, name: str) -> None:
    result = _fetch(sub.cas)
    value = _value(result, name)
    low, high = sub.ranges[name]
    assert value is not None, f"{sub.name}: {name} is None; warnings: {result['warnings']}"
    assert low <= value <= high, f"{sub.name}: {name}={value} outside [{low}, {high}] ({UNITS})"


@pytest.mark.parametrize(
    ("sub", "name"),
    [(s, n) for s in SUBSTANCES for n in s.absent],
    ids=lambda v: v if isinstance(v, str) else v.name,
)
def test_expected_absent_has_warning(sub: Expected, name: str) -> None:
    result = _fetch(sub.cas)
    assert _value(result, name) is None
    assert any(w.startswith(f"{name}:") for w in result["warnings"])


@pytest.mark.parametrize("sub", SUBSTANCES, ids=lambda s: s.name)
def test_every_value_has_a_source_and_every_missing_one_a_warning(sub: Expected) -> None:
    result = _fetch(sub.cas)
    for name in ("vapor_pressure", "density", "rfd", "rfc", "sf", "iur"):
        if _value(result, name) is None:
            assert any(w.startswith(f"{name}:") for w in result["warnings"]), name
        else:
            assert name in result["sources"], name


APPLIED_ROUTE = {"rfd": "oral", "rfc": "inhalation", "sf": "oral", "iur": "inhalation"}
CANCER = {"sf", "iur"}


@pytest.mark.parametrize("sub", SUBSTANCES, ids=lambda s: s.name)
def test_toxicity_details_are_consistent_with_values(sub: Expected) -> None:
    result = _fetch(sub.cas)
    details = result["toxicity_details"]
    found = {n for n in APPLIED_ROUTE if _value(result, n) is not None}
    assert set(details) == found
    for name, detail in details.items():
        assert detail["exposure_route"] == APPLIED_ROUTE[name]
        assert detail["source"] == result["sources"][name]
        assert detail["assessment"] in {"cancer", "non-cancer", None}
        assert detail["route_reported"]
        if name in CANCER:
            assert detail["assessment"] in {"cancer", None}


def test_benzene_cancer_endpoint_and_routes() -> None:
    details = _fetch("71-43-2")["toxicity_details"]
    for name in ("sf", "iur"):
        assert details[name]["source"] == "IRIS"
        assert details[name]["assessment"] == "cancer"
        assert "leukemia" in (details[name]["endpoint"] or "").lower()
    assert details["sf"]["exposure_route"] == "oral"
    assert details["iur"]["exposure_route"] == "inhalation"
    assert details["rfc"]["assessment"] == "non-cancer"
    assert "lymphocyte" in (details["rfc"]["endpoint"] or "").lower()


def test_reported_route_may_differ_from_applied_route() -> None:
    """Formaldehyde's RfC only exists from a source that does not state a route."""
    detail = _fetch("50-00-0")["toxicity_details"]["rfc"]
    assert detail["exposure_route"] == "inhalation"
    assert detail["route_reported"] == "not specified"


@pytest.mark.parametrize("cas", ["0-00-0", "71-43-3"])
def test_invalid_cas_returns_warning_not_error(cas: str) -> None:
    result = _fetch(cas)
    assert result["molecular_weight"] is None
    assert result["sources"] == {}
    assert any("could not be resolved" in w for w in result["warnings"])


def test_bare_number_cas_resolves_to_the_right_chemical() -> None:
    """A bare '71432' is a substance ID to CompTox's search; it must be hyphenated first."""
    result = _fetch("71432")
    assert result["molecular_weight"] == pytest.approx(78.11, abs=0.05)
    assert _value(result, "vapor_pressure") is not None
    assert 50.0 <= (_value(result, "vapor_pressure") or 0.0) <= 150.0


def test_valid_but_unknown_cas_returns_warning_not_error() -> None:
    result = _fetch("99999-99-2")  # valid check digit, assigned to no chemical
    assert result["molecular_weight"] is None
    assert any("could not be resolved" in w for w in result["warnings"])
