"""Projectors of the exposure tools: meteorology, population and the exposure result."""

from __future__ import annotations

from api.services.projectors.ledger import Ledger, Located, Receptor, ToolExchange, number
from api.services.projectors.payloads import (
    ExposurePayload,
    MeteorologyPayload,
    PopulationPayload,
)


def _point(exchange: ToolExchange) -> tuple[float, float] | None:
    latitude, longitude = number(exchange.args, "latitude"), number(exchange.args, "longitude")
    if latitude is None or longitude is None:
        return None
    return (latitude, longitude) if abs(latitude) <= 90 and abs(longitude) <= 180 else None


def project_meteorology(exchange: ToolExchange, ledger: Ledger) -> None:
    """The weather at the point the model asked about."""
    point = _point(exchange)
    if point is None:
        ledger.skip(exchange, "the point asked about was not valid")
        return
    result = ledger.read(exchange, MeteorologyPayload)
    if result is not None:
        ledger.meteorology.append(Located(*point, result))


def project_population(exchange: ToolExchange, ledger: Ledger) -> None:
    """The residents around the point asked about, within the radius asked for (or the default)."""
    point = _point(exchange)
    if point is None:
        ledger.skip(exchange, "the point asked about was not valid")
        return
    radius = number(exchange.args, "radius_km")
    result = ledger.read(exchange, PopulationPayload)
    if result is not None:
        radius_km = ledger.default_radius_km if radius is None else radius
        ledger.population.append(Receptor(Located(*point, result), radius_km))


def project_exposure(exchange: ToolExchange, ledger: Ledger) -> None:
    """The exposure result, tied to the emission rate the model passed."""
    rate = number(exchange.args, "emission_rate")
    result = ledger.read(exchange, ExposurePayload)
    if result is not None and rate is not None:
        ledger.exposures.append((rate, result))
