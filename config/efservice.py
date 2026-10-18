"""Typed loaders for the Envirofacts ``[efservice]`` and ``[frs]`` settings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import read_toml, require_int, require_number, require_str, section


@dataclass(frozen=True)
class EfserviceSettings:
    """How every EPA Envirofacts (``efservice``) request is made.

    Attributes:
        base_url: Service root URL, without trailing slash.
        delay_seconds: Wait before each request, in seconds.
        timeout_seconds: Per-request timeout, in seconds.
        max_retries: Retries after a throttled, failed or timed-out request.
        backoff_seconds: First retry wait in seconds; doubles on each further retry.
    """

    base_url: str
    delay_seconds: float
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float

    def url(self, path: str) -> str:
        """Return ``path`` (starting with ``/``) appended to the base URL."""
        return self.base_url.rstrip("/") + path


@dataclass(frozen=True)
class FrsSettings:
    """The FRS-to-EIS query (``FRS_PROGRAM_FACILITY`` table).

    Attributes:
        eis_path: Path template appended to the base URL; contains ``{frs_id}``.
        program: Program acronym that marks an EIS registration, e.g. ``"EIS"``.
        registry_field: Response column holding the FRS registry ID.
        program_field: Response column holding the program acronym.
        eis_id_field: Response column holding the EIS facility ID.
    """

    eis_path: str
    program: str
    registry_field: str
    program_field: str
    eis_id_field: str


def load_efservice_settings(path: Path | None = None) -> EfserviceSettings:
    """Load and validate the shared Envirofacts request settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), "efservice")
    name = "efservice"
    return EfserviceSettings(
        base_url=require_str(table, "base_url", name),
        delay_seconds=require_number(table, "delay_seconds", minimum=0, name=name),
        timeout_seconds=require_number(table, "timeout_seconds", minimum=0.001, name=name),
        max_retries=require_int(table, "max_retries", minimum=0, name=name),
        backoff_seconds=require_number(table, "backoff_seconds", minimum=0, name=name),
    )


def load_frs_settings(path: Path | None = None) -> FrsSettings:
    """Load and validate the FRS-to-EIS query settings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid, or the path lacks ``{frs_id}``.
    """
    table = section(read_toml(path), "frs")
    eis_path = require_str(table, "eis_path", "frs")
    if "{frs_id}" not in eis_path:
        raise ValueError("frs.eis_path must contain {frs_id}")
    return FrsSettings(
        eis_path=eis_path,
        program=require_str(table, "program", "frs").strip(),
        registry_field=require_str(table, "registry_field", "frs").strip(),
        program_field=require_str(table, "program_field", "frs").strip(),
        eis_id_field=require_str(table, "eis_id_field", "frs").strip(),
    )


@lru_cache(maxsize=1)
def get_efservice_settings() -> EfserviceSettings:
    """Return the cached Envirofacts settings from the default file."""
    return load_efservice_settings()


@lru_cache(maxsize=1)
def get_frs_settings() -> FrsSettings:
    """Return the cached FRS settings from the default file."""
    return load_frs_settings()
