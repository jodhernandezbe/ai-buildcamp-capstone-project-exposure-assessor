"""Chemical property lookup tool."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import ChemicalProperties


@tool
def fetch_chemical_properties(cas_number: str) -> ChemicalProperties:
    """Fetch physical-chemical properties and inhalation toxicity values for a chemical.

    Purpose:
        Use this first when assessing a chemical. The values it returns feed the
        dispersion and risk steps (`calculate_exposure_metrics`).

    Args:
        cas_number: CAS registry number, e.g. "71-43-2" for benzene.

    Returns:
        A dict with:
        - molecular_weight: g/mol
        - vapor_pressure: mmHg at 25 C
        - rfc: inhalation reference concentration, mg/m3 (non-cancer benchmark)
        - iur: inhalation unit risk, per ug/m3 (cancer potency)
    """
    raise NotImplementedError
