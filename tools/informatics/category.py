"""TRI category tool: which TRI categories list a chemical (membership only, no estimate)."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import TriCategoryResult
from tools.tri_categories import category_refs, get_category_index


@tool
def find_tri_category(cas_number: str) -> TriCategoryResult:
    """Find the TRI categories that list a chemical (a category member is not listed on its own).

    Purpose:
        Applies only to a chemical already identified by a CAS number the user gave. TRI reports
        some chemicals only as members of a category (for example lead compounds, N420) instead
        of under their own CAS number. If `categories` is not empty, the chemical
        is not listed in TRI on its own but is reported through those categories. Say so, name the
        category, and say that its releases cover every member of the category together, not this
        chemical alone. Membership is a listing fact, not an estimate: no similarity is involved.
        An empty `categories` means the chemical is in no category; then nothing here is known
        about its TRI reporting.

    Args:
        cas_number: CAS registry number as the user gave it, e.g. "95-57-8" (hyphens optional).
            Never a number recalled from a chemical's name: if the user gave only a name, ask for
            the CAS number instead of calling this tool.

    Returns:
        A dict with:
        - query_cas: the CAS number as given, whitespace stripped
        - categories: every TRI category that lists it, each with `code` (e.g. "N084") and
          `name`; empty if none does
        - warnings: why the lookup could not be made, e.g. the CAS number is not valid
    """
    lookup = get_category_index().lookup(cas_number)
    return {
        "query_cas": cas_number.strip(),
        "categories": category_refs(lookup.categories),
        "warnings": list(lookup.warnings),
    }
