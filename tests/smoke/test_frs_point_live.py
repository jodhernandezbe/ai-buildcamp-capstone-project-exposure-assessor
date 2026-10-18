"""Live smoke test for FrsLocator against EPA Envirofacts (no key needed).

Run with ``uv run pytest -m smoke``. The FRS ID is a real facility whose TRI rows carry no
coordinates for the formaldehyde inventory (Puerto Rico).
"""

from __future__ import annotations

import httpx
import pytest

from config.efservice import get_efservice_settings
from config.frs_point import get_frs_point_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.inventory.frs_point import FrsLocator

pytestmark = pytest.mark.smoke


def test_frs_gives_the_coordinates_tri_lacks() -> None:
    with httpx.Client() as http:
        locator = FrsLocator(
            EfserviceClient(get_efservice_settings(), http), get_frs_point_settings()
        )
        found = locator("110012141805")
    assert found is not None
    assert 17.0 < found.latitude < 19.0 and -68.0 < found.longitude < -65.0
