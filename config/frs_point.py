"""Settings of the FRS facility-coordinates query (``GEO_FACILITY_POINT`` table)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import read_toml, require_str, section


@dataclass(frozen=True)
class FrsPointSettings:
    """Where to read a facility's coordinates when TRI has none.

    Attributes:
        path: Path template appended to the Envirofacts base URL; contains ``{frs_id}``.
        latitude_field: Response column with the latitude, decimal degrees.
        longitude_field: Response column with the longitude, decimal degrees (west negative).
        timestamp_field: Response column used to prefer the newest point.
    """

    path: str
    latitude_field: str
    longitude_field: str
    timestamp_field: str


def load_frs_point_settings(path: Path | None = None) -> FrsPointSettings:
    """Load and validate the ``[frs_point]`` table.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid, or the path lacks ``{frs_id}``.
    """
    table = section(read_toml(path), "frs_point")
    query = require_str(table, "path", "frs_point")
    if "{frs_id}" not in query:
        raise ValueError("frs_point.path must contain {frs_id}")
    return FrsPointSettings(
        path=query,
        latitude_field=require_str(table, "latitude_field", "frs_point").strip(),
        longitude_field=require_str(table, "longitude_field", "frs_point").strip(),
        timestamp_field=require_str(table, "timestamp_field", "frs_point").strip(),
    )


@lru_cache(maxsize=1)
def get_frs_point_settings() -> FrsPointSettings:
    """Return the cached FRS point settings from the default file."""
    return load_frs_point_settings()
