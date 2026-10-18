"""Facility industry tool: the TRI control number of an emission record -> its industry title."""

from __future__ import annotations

import httpx
from langchain_core.tools import tool

from config.efservice import get_efservice_settings
from config.industry import get_industry_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.industry.naics import submission_industry
from tools.schemas import FacilityIndustry


def _open_client() -> httpx.Client:
    """Create the HTTP client (the edge where the default collaborator is built)."""
    return httpx.Client()


@tool
def fetch_facility_industry(doc_ctrl_num: str | int) -> FacilityIndustry:
    """Fetch the industry behind an emission record, as a title in words.

    Purpose:
        Use this to learn what kind of facility reported an emission record, from that
        record's `doc_ctrl_num` (the TRI control number the emissions inventory returns with
        each record, identifying the submission whose year the record reports). The
        `naics_title` (for example "Petroleum Refineries") is exactly the text the SCC
        process search needs to suggest the processes that likely emit and, from them, a
        process-typical stack; the numeric code alone is useless there. It costs two requests
        per record, so call it only for facilities you are assessing, and only when you need
        the industry (for example because the facility has no stack of its own in the NEI).
        An industry says what a facility makes, not which unit emits, so treat what you derive
        from it as a candidate. If the industry is unknown (null title), do not guess one:
        call `fetch_stack_parameters_from_scc` without a code to get the EPA global default
        stack, and say that the stack is generic.

    Args:
        doc_ctrl_num: The `doc_ctrl_num` of the facility's emission record (digits; a number
            is also accepted).

    Returns:
        A dict with:
        - naics_code: the submission's primary six-digit NAICS code, or null
        - naics_title: the title of that code in words, or null; this is what to pass on
        - code_origin: "reported" when the facility gave the code (from reporting year 2006),
          "assigned" when EPA assigned it (older submissions; often a generic code such as
          "All Other Miscellaneous Manufacturing"), or null if unknown
        - source: where it comes from ("TRI submission NAICS"), or null when nothing was found
        - warnings: why a value is null (invalid number, no NAICS in TRI, a placeholder code,
          TRI unreachable), that EPA assigned the code, or that a code has no title yet; a
          null result is not an error: say the industry is unknown and do not guess it
    """
    with _open_client() as http:
        client = EfserviceClient(get_efservice_settings(), http)
        return submission_industry(doc_ctrl_num, client, get_industry_settings())
