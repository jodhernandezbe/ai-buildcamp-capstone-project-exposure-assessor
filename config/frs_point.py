"""Settings of the bulk FRS facility-coordinates query (``mv_new_geo_best_picks`` lookup)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import read_toml, require_int, require_str, section

_NAME = "frs_point"


@dataclass(frozen=True)
class FrsPointSettings:
    """Where to read facility coordinates when TRI has none, many facilities per request.

    Attributes:
        base_url: Service root URL (a different service from Envirofacts ``efservice``).
        path: Path template appended to ``base_url``; contains ``{frs_ids}``, a comma-separated
            list of FRS IDs.
        registry_field: Answer column holding the FRS ID of the row.
        latitude_field: Answer column with the latitude, decimal degrees.
        longitude_field: Answer column with the longitude, decimal degrees (west negative).
        batch_size: Most FRS IDs asked in one request.
    """

    base_url: str
    path: str
    registry_field: str
    latitude_field: str
    longitude_field: str
    batch_size: int


def load_frs_point_settings(path: Path | None = None) -> FrsPointSettings:
    """Load and validate the ``[frs_point]`` table.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid, or the path lacks ``{frs_ids}``.
    """
    table = section(read_toml(path), _NAME)
    query = require_str(table, "path", _NAME)
    if "{frs_ids}" not in query:
        raise ValueError("frs_point.path must contain {frs_ids}")
    return FrsPointSettings(
        base_url=require_str(table, "base_url", _NAME).strip(),
        path=query,
        registry_field=require_str(table, "registry_field", _NAME).strip(),
        latitude_field=require_str(table, "latitude_field", _NAME).strip(),
        longitude_field=require_str(table, "longitude_field", _NAME).strip(),
        batch_size=require_int(table, "batch_size", minimum=1, name=_NAME),
    )


@lru_cache(maxsize=1)
def get_frs_point_settings() -> FrsPointSettings:
    """Return the cached FRS point settings from the default file."""
    return load_frs_point_settings()
