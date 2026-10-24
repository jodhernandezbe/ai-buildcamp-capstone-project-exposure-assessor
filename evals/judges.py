"""LLM judge criteria: each answers one narrow PASS/FAIL question about the final report."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Judge:
    """One PASS/FAIL criterion about the final report."""

    name: str
    criteria: str


ASKS_FOR_CAS = Judge(
    name="asks for CAS without inventing one",
    criteria=(
        "The text is an exposure assessor's reply to a user who named a chemical "
        "only by its common name. PASS only if the reply asks the user to provide "
        "the chemical's CAS registry number AND does not itself state a CAS number "
        "(a pattern like 50-00-0) AND does not present any facility, concentration, "
        "or risk result. Otherwise FAIL."
    ),
)

CATEGORY_MATCH_DISCLOSED = Judge(
    name="category match disclosed",
    criteria=(
        "The text is a screening-level assessment report for a chemical that TRI does not list "
        "on its own but reports as a member of a TRI category. PASS only if ALL of these hold: "
        "(1) it says the chemical was matched through a TRI category and names that category; "
        "(2) it says the reported releases cover every member of the category together, so they "
        "are not a measured release of this one chemical; (3) it does not present a "
        "structurally similar chemical's value as this chemical's own measured value. "
        "Otherwise FAIL."
    ),
)

COMPLETE_ASSESSMENT_REPORT = Judge(
    name="complete assessment report",
    criteria=(
        "The text is a screening-level exposure and risk assessment report for a chemical "
        "released by industrial facilities. PASS only if ALL of these hold: (1) it opens with "
        "a short summary of what was assessed and the main finding; (2) it gives a table "
        "of results with units, one row per facility assessed, or, when every facility was "
        "screened out, the facilities closest to a threshold with their screening values; "
        "(3) where a facility has several stacks it shows the range of results over the "
        "stacks, not a single stack; (4) for each facility assessed in full it reports both "
        "a worst-case and a representative (typical-weather) result; (5) it says where each "
        "input came from (for example NEI stacks, the weather data, the census data, the "
        "toxicity database); (6) it has a Limitations section stating the method's limits "
        "and the data gaps. Otherwise FAIL."
    ),
)
