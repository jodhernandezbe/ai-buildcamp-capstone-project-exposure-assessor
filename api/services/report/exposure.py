"""Section 5: per facility, the stacks, weather and residents behind the modelled exposure."""

from __future__ import annotations

from docx.document import Document

from api.schemas.workspace import (
    Dose,
    ExposureRanges,
    Extreme,
    Facility,
    Meteorology,
    Receptors,
    Stack,
    WorkspaceState,
)
from api.services.report.document import (
    ReportContext,
    empty,
    facility_label,
    paragraph,
    subheading,
    table,
)
from config.exposure import get_exposure_settings

_STACK_HEADER = (
    "Stack",
    "Height",
    "Diameter",
    "Exit velocity",
    "Exit temperature",
    "Tier",
    "Source",
)
_CONCENTRATION = "µg/m³"
_DOSE = "mg/(kg·day)"
_DEFAULT = " (screening default)"


def _stack(stack: Stack, ctx: ReportContext) -> list[str]:
    fmt = ctx.fmt
    return [
        str(stack.stack_number) if stack.stack_number is not None else fmt.absent(),
        fmt.number(stack.height_m, "m"),
        fmt.number(stack.diameter_m, "m"),
        fmt.number(stack.exit_velocity_m_s, "m/s"),
        fmt.number(stack.exit_temperature_k, "K"),
        fmt.text(stack.tier_label),
        fmt.text(stack.source),
    ]


def _span(extreme: Extreme | None, ctx: ReportContext) -> str:
    if extreme is None:
        return ctx.fmt.absent()
    return ctx.fmt.span(extreme.low, extreme.high, _CONCENTRATION)


def _ranges(exposure: ExposureRanges | None, ctx: ReportContext) -> list[list[str]]:
    if exposure is None:
        return [["Modelled concentrations", ctx.fmt.absent()]]
    evaluated = f"{exposure.stacks_evaluated} of {exposure.stacks_given}"
    return [
        ["Stacks evaluated", evaluated],
        ["Worst-case maximum concentration", _span(exposure.concentration_worst, ctx)],
        ["Representative maximum concentration", _span(exposure.concentration_representative, ctx)],
    ]


def _weather(met: Meteorology | None, ctx: ReportContext) -> list[list[str]]:
    fmt = ctx.fmt
    if met is None:
        return [["Meteorology", fmt.absent()]]
    return [
        ["Wind speed", fmt.number(met.wind_speed_m_s, "m/s")],
        ["Wind from", fmt.number(met.wind_from_deg, "°")],
        ["Ambient temperature", fmt.number(met.ambient_temperature_k, "K")],
        ["Stability class", fmt.text(met.stability_class)],
        ["Meteorology source", met.source + (_DEFAULT if met.screening_default else "")],
    ]


def _people(receptors: Receptors | None, ctx: ReportContext) -> list[list[str]]:
    fmt = ctx.fmt
    if receptors is None:
        return [["Receptor population", fmt.absent()]]
    default = _DEFAULT if receptors.screening_default else ""
    return [
        ["Receptor radius", fmt.number(receptors.radius_km, "km")],
        ["Population within the radius", fmt.count(receptors.total_population)],
        ["Receptor source", receptors.source + default],
    ]


def _dose(dose: Dose | None, ctx: ReportContext) -> list[list[str]]:
    """The worst-case inhalation dose of each age band, the most exposed one marked."""
    if dose is None or not dose.by_band:
        return [["Inhalation dose by age band", ctx.fmt.absent()]]
    return [
        [
            f"Average daily dose, age {band}" + (" (highest)" if band == dose.highest_band else ""),
            ctx.fmt.number(value, _DOSE),
        ]
        for band, value in dose.by_band.items()
    ]


def _band_row(band: str, rate: float, weight: float, ctx: ReportContext) -> list[str]:
    fmt = ctx.fmt
    return [
        f"Age {band}: inhalation rate, body weight",
        f"{fmt.number(rate, 'm³/day')}, {fmt.number(weight, 'kg')}",
    ]


def _assumptions(doc: Document, ctx: ReportContext) -> None:
    """The resident-air exposure factors and inhalation rates the doses and risks rest on."""
    settings = get_exposure_settings()
    f, fmt = settings.factors, ctx.fmt
    rows = [
        ["Exposure time", fmt.number(f.exposure_time_hours_per_day, "h/day")],
        ["Exposure frequency", fmt.number(f.exposure_frequency_days_per_year, "days/yr")],
        ["Exposure duration", fmt.number(f.exposure_duration_years, "yr")],
        ["Lifetime (cancer averaging time)", fmt.number(f.lifetime_years, "yr")],
        *(
            _band_row(band, v.inhalation_rate_m3_per_day, v.body_weight_kg, ctx)
            for band, v in settings.age_bands.items()
        ),
    ]
    subheading(doc, "Inhalation exposure assumptions")
    table(doc, ("Item", "Value"), rows)


def _facility(doc: Document, facility: Facility, ctx: ReportContext) -> None:
    subheading(doc, facility_label(facility))
    if facility.stacks:
        table(doc, _STACK_HEADER, [_stack(s, ctx) for s in facility.stacks])
    else:
        paragraph(doc, f"Stack parameters: {ctx.fmt.absent()}")
    rows = [
        *_ranges(facility.exposure, ctx),
        *_weather(facility.meteorology, ctx),
        *_people(facility.receptors, ctx),
        *_dose(facility.exposure.dose if facility.exposure else None, ctx),
    ]
    table(doc, ("Item", "Value"), rows)


def write_exposure(doc: Document, state: WorkspaceState, ctx: ReportContext) -> None:
    """One subsection per facility, or the empty-section sentence."""
    if not state.facilities:
        empty(doc, ctx)
        return
    for facility in state.facilities:
        _facility(doc, facility, ctx)
    _assumptions(doc, ctx)
