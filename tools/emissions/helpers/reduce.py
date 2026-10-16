"""Validate TRI release rows and keep the latest reporting year per medium and facility."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import NamedTuple, TypedDict

from commons.units import UnitConversionError
from config.loader import EmissionsSettings, TriSettings
from tools.emissions.helpers.rate import operating_hours_per_year, to_emission_rate
from tools.schemas import EmissionRecord

Row = Mapping[str, object]


@dataclass(frozen=True)
class Location:
    """Facility coordinates, in decimal degrees (north positive, west negative)."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class Place:
    """Descriptive facility fields taken from a report row."""

    name: str | None
    address: str | None
    city: str | None
    county: str | None
    state: str | None
    zip_code: str | None


@dataclass(frozen=True)
class Report:
    """One validated TRI row. ``quantity`` is None unless it is a usable amount with a unit."""

    facility_id: str
    medium: str
    year: int
    quantity: float | None
    unit: str | None
    place: Place
    location: Location | None


@dataclass
class Slot:
    """What is kept for one (medium, facility): its latest year and best coordinates."""

    year: int
    quantity: float | None
    unit: str | None
    summed: int  # number of usable quantities added into `quantity`
    place: Place
    location: Location | None
    location_year: int


class _Amount(NamedTuple):
    """A slot's usable quantity, its unit as reported, and its coordinates."""

    quantity: float
    unit: str
    location: Location


@dataclass
class Stats:
    """Counts of what was dropped or combined, for warnings."""

    skipped_rows: int = 0
    no_quantity: int = 0
    no_location: int = 0
    bad_unit: int = 0
    mixed_units: int = 0
    combined: int = 0

    def warnings(self) -> list[str]:
        """Return one message per non-zero count."""
        labels = (
            ("skipped_rows", "rows skipped (no facility ID or year, or a medium not configured)"),
            ("no_quantity", "facilities omitted: no usable release quantity in their latest year"),
            ("no_location", "facilities omitted: no usable coordinates in any row"),
            ("bad_unit", "facilities omitted: release unit is not a convertible mass unit"),
            ("mixed_units", "same-year reports ignored: unit differs from the first report"),
            ("combined", "facilities whose latest-year reports were added together"),
        )
        return [f"{getattr(self, key)} {text}" for key, text in labels if getattr(self, key)]


def _text(value: object) -> str | None:
    """Return ``value`` stripped if it is non-blank text, else None."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _finite(value: object) -> float | None:
    """Return ``value`` as a float if it is a finite number (not a bool), else None."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _year(value: object) -> int | None:
    """Return a reporting year from a digit string or integer, else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = _text(value)
    return int(text) if text is not None and text.isascii() and text.isdigit() else None


def _quantity(row: Row, settings: TriSettings) -> tuple[float | None, str | None]:
    """Return (quantity, unit); the quantity is None unless finite, non-negative, with a unit."""
    unit = _text(row.get(settings.fields["unit"]))
    amount = _finite(row.get(settings.fields["quantity"]))
    if unit is None or amount is None or amount < 0:
        return None, unit
    return amount, unit


def _facility_id(row: Row, settings: TriSettings) -> str | None:
    for column in settings.facility_id_fields:
        identifier = _text(row.get(column))
        if identifier is not None:
            return identifier
    return None


def _signed_longitude(magnitude: float, state: str | None, settings: TriSettings) -> float | None:
    """Return the signed longitude, or None when the hemisphere cannot be determined.

    TRI gives western longitudes as positive numbers; only the configured east-of-Greenwich
    states keep a positive sign.
    """
    if state is None:
        return None
    east = {code.upper() for code in settings.east_longitude_states}
    return abs(magnitude) if state.upper() in east else -abs(magnitude)


def _location(row: Row, settings: TriSettings) -> Location | None:
    fields = settings.fields
    latitude = _finite(row.get(fields["latitude"]))
    raw_longitude = _finite(row.get(fields["longitude"]))
    if latitude is None or raw_longitude is None:
        return None
    state = _text(row.get(fields["state"]))
    longitude = _signed_longitude(raw_longitude, state, settings)
    if longitude is None or not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return None
    return Location(latitude, longitude)


def _place(row: Row, settings: TriSettings) -> Place:
    def get(key: str) -> str | None:
        return _text(row.get(settings.fields[key]))

    return Place(
        get("facility_name"),
        get("address"),
        get("city"),
        get("county"),
        get("state"),
        get("zip_code"),
    )


def parse_report(row: Row, settings: TriSettings) -> Report | None:
    """Validate one TRI row.

    Args:
        row: A row of the joined TRI release query (untrusted).
        settings: TRI settings naming the columns to read.

    Returns:
        The report, or None if the row has no facility ID, medium or reporting year. An
        unusable quantity or location does not drop the row here: it is carried as None.
    """
    facility_id = _facility_id(row, settings)
    medium = _text(row.get(settings.fields["medium"]))
    year = _year(row.get(settings.fields["year"]))
    if facility_id is None or medium is None or year is None:
        return None
    quantity, unit = _quantity(row, settings)
    return Report(
        facility_id, medium, year, quantity, unit, _place(row, settings), _location(row, settings)
    )


def _new_slot(report: Report) -> Slot:
    return Slot(
        year=report.year,
        quantity=report.quantity,
        unit=report.unit,
        summed=0 if report.quantity is None else 1,
        place=report.place,
        location=report.location,
        location_year=report.year,
    )


def _take_year(slot: Slot, report: Report) -> None:
    """Make ``report`` (a later year) the slot's year-level data."""
    slot.year = report.year
    slot.quantity = report.quantity
    slot.unit = report.unit
    slot.summed = 0 if report.quantity is None else 1
    slot.place = report.place


class LatestReports:
    """Folds report rows into one record per (medium, facility) at its latest year.

    Reports of the same facility, medium and year are added together (separate forms with
    different quantities; summing is the conservative choice). Coordinates come from the
    facility's most recent row that has valid ones, since the latest row often lacks them.
    """

    def __init__(self, settings: TriSettings) -> None:
        self._settings = settings
        self._slots: dict[tuple[str, str], Slot] = {}
        self.stats = Stats()

    def add_rows(self, rows: Sequence[Row]) -> None:
        """Fold a page of rows into the running result."""
        for row in rows:
            self._add(row)

    def _add(self, row: Row) -> None:
        report = parse_report(row, self._settings)
        if report is None or report.medium not in self._settings.media:
            self.stats.skipped_rows += 1
            return
        key = (report.medium, report.facility_id)
        slot = self._slots.get(key)
        if slot is None:
            self._slots[key] = _new_slot(report)
            return
        self._merge(slot, report)

    def _merge(self, slot: Slot, report: Report) -> None:
        if report.year > slot.year:
            _take_year(slot, report)
        elif report.year == slot.year:
            self._combine(slot, report)
        if report.location is not None and (
            slot.location is None or report.year > slot.location_year
        ):
            slot.location, slot.location_year = report.location, report.year

    def _combine(self, slot: Slot, report: Report) -> None:
        if report.quantity is None:
            return
        if slot.quantity is None:
            slot.quantity, slot.unit, slot.summed = report.quantity, report.unit, 1
        elif slot.unit != report.unit:
            self.stats.mixed_units += 1
        else:
            slot.quantity += report.quantity
            slot.summed += 1

    def records(
        self, emissions: EmissionsSettings, aliases: Mapping[str, str] | None = None
    ) -> list[EmissionRecord]:
        """Return the kept records, converting each release to an emission rate.

        Args:
            emissions: Emission-rate assumptions (operating hours per year).
            aliases: Source unit spelling -> Pint-parsable unit string.

        Returns:
            One record per (medium, facility) with a usable latest-year quantity and
            coordinates; the others are counted in ``stats``.
        """
        hours = operating_hours_per_year(emissions)
        found = (self._record(key, slot, hours, aliases) for key, slot in self._slots.items())
        records = [record for record in found if record is not None]
        self.stats.combined = sum(slot.summed > 1 for slot in self._slots.values())
        return records

    def _amount(self, slot: Slot) -> _Amount | None:
        """Return the slot's quantity, unit and location, or count why it is unusable."""
        if slot.quantity is None or slot.unit is None:
            self.stats.no_quantity += 1
        elif slot.location is None:
            self.stats.no_location += 1
        else:
            return _Amount(slot.quantity, slot.unit, slot.location)
        return None

    def _record(
        self, key: tuple[str, str], slot: Slot, hours: float, aliases: Mapping[str, str] | None
    ) -> EmissionRecord | None:
        amount = self._amount(slot)
        if amount is None:
            return None
        try:
            rate = to_emission_rate(amount.quantity, amount.unit, hours, aliases)
        except UnitConversionError:
            self.stats.bad_unit += 1
            return None
        return EmissionRecord(
            **_reported(key, slot, amount, rate, hours), **_where(slot.place, amount.location)
        )


class _Reported(TypedDict):
    frs_id: str
    facility_name: str | None
    environmental_medium: str
    reporting_year: int
    total_release: float
    unit: str
    emission_rate: float
    operating_hours_per_year: float


class _Where(TypedDict):
    latitude: float
    longitude: float
    address: str | None
    city: str | None
    county: str | None
    state: str | None
    zip_code: str | None


def _reported(
    key: tuple[str, str], slot: Slot, amount: _Amount, rate: float, hours: float
) -> _Reported:
    medium, facility_id = key
    return {
        "frs_id": facility_id,
        "facility_name": slot.place.name,
        "environmental_medium": medium,
        "reporting_year": slot.year,
        "total_release": amount.quantity,
        "unit": amount.unit,
        "emission_rate": rate,
        "operating_hours_per_year": hours,
    }


def _where(place: Place, location: Location) -> _Where:
    return {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "address": place.address,
        "city": place.city,
        "county": place.county,
        "state": place.state,
        "zip_code": place.zip_code,
    }
