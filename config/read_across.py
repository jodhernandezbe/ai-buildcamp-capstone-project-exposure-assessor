"""Typed loader for the ``[read_across]`` settings (TRI read-across surrogate tool)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from config.parsing import (
    names,
    project_path,
    read_toml,
    require_bool,
    require_fraction,
    require_int,
    require_number,
    require_str,
    section,
    subtable,
)

_NAME = "read_across"


@dataclass(frozen=True)
class PubchemSettings:
    """How a chemical's SMILES and molecular weight are read from PubChem PUG REST.

    Attributes:
        url_template: Full URL with ``{cas}``, the CAS number looked up by name.
        smiles_properties: Response properties tried in order for the SMILES.
        weight_property: Response property holding the molecular weight, in g/mol.
        delay_seconds: Wait before each request, in seconds.
        timeout_seconds: Per-request timeout, in seconds.
        max_retries: Retries after a throttled, failed or timed-out request.
        backoff_seconds: First retry wait in seconds; doubles on each further retry.
    """

    url_template: str
    smiles_properties: tuple[str, ...]
    weight_property: str
    delay_seconds: float
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float

    def url(self, cas: str) -> str:
        """Return the lookup URL for ``cas`` (URL-encoded)."""
        return self.url_template.format(cas=quote(cas, safe=""))


@dataclass(frozen=True)
class ModelSettings:
    """The SMILES encoder.

    Attributes:
        name: Hugging Face model id.
        revision: Pinned model commit.
        max_length: Longest tokenized SMILES, in tokens (longer ones are truncated).
        embedding_width: Length of one embedding vector.
    """

    name: str
    revision: str
    max_length: int
    embedding_width: int


@dataclass(frozen=True)
class FingerprintSettings:
    """Morgan fingerprint: ``radius`` bonds around each atom, folded to ``n_bits`` bits."""

    radius: int
    n_bits: int


@dataclass(frozen=True)
class CatalogColumns:
    """Column names of the read-across catalog (the last two are optional columns)."""

    cas: str
    name: str
    smiles: str
    molecular_weight: str
    embedding: str
    bits: str
    benchmark_flag: str
    naics_prefixes: str


@dataclass(frozen=True)
class TriListSettings:
    """Where the current TRI chemical list is read from (Envirofacts ``tri_chem_info``).

    Attributes:
        path: Path appended to the Envirofacts base URL; contains ``{start}`` and ``{end}``
            (first and last row, inclusive).
        page_size: Rows requested per page.
        cas_field: Response field holding the CAS number (or a group code).
        name_field: Response field holding the chemical name.
        inactive_field: Response field holding the year the chemical left TRI.
        active_value: Value of ``inactive_field`` for a chemical still listed.
        keep_delisted: Whether chemicals no longer listed are kept.
    """

    path: str
    page_size: int
    cas_field: str
    name_field: str
    inactive_field: str
    active_value: str
    keep_delisted: bool

    def page_path(self, start: int) -> str:
        """Return the path of the page whose first row is ``start``."""
        return self.path.format(start=start, end=start + self.page_size - 1)


@dataclass(frozen=True)
class ReadAcrossSettings:
    """All read-across settings.

    Attributes:
        directory: Folder of catalog shard files, absolute or resolved against the project
            root.
        file_template: Shard file name, containing ``{prefix}``.
        prefix_digits: Number of leading CAS digits that name a shard.
        alpha: Weight of the embedding cosine in the hybrid score, in [0, 1].
        min_hybrid_score: Lowest hybrid score inside the applicability domain, in [0, 1].
    """

    directory: Path
    file_template: str
    prefix_digits: int
    alpha: float
    min_hybrid_score: float
    pubchem: PubchemSettings
    model: ModelSettings
    fingerprint: FingerprintSettings
    columns: CatalogColumns
    tri_list: TriListSettings

    def shard_path(self, prefix: str) -> Path:
        """Return the shard file for a CAS-number prefix."""
        return self.directory / self.file_template.format(prefix=prefix)

    def shard_prefix(self, cas: str) -> str:
        """Return the shard prefix a CAS number belongs to (its leading digits)."""
        return cas[: self.prefix_digits]

    def shard_paths(self) -> tuple[Path, ...]:
        """Return the existing shard files, in prefix order."""
        pattern = self.file_template.format(prefix="*")
        return tuple(sorted(self.directory.glob(pattern)))


def _url_template(table: dict[str, object], name: str) -> str:
    template = require_str(table, "url_template", name).strip()
    try:
        template.format(cas="0")
    except (KeyError, IndexError, ValueError) as exc:
        raise ValueError(f"{name}.url_template must contain only the {{cas}} slot") from exc
    if "{cas}" not in template:
        raise ValueError(f"{name}.url_template must contain {{cas}}")
    return template


def _shard_template(table: dict[str, object]) -> str:
    template = require_str(table, "file_template", _NAME).strip()
    if "{prefix}" not in template:
        raise ValueError(f"{_NAME}.file_template must contain {{prefix}}")
    return template


def _pubchem(table: dict[str, object]) -> PubchemSettings:
    name = f"{_NAME}.pubchem"
    return PubchemSettings(
        url_template=_url_template(table, name),
        smiles_properties=names(table, "smiles_properties", name, allow_empty=False),
        weight_property=require_str(table, "weight_property", name).strip(),
        delay_seconds=require_number(table, "delay_seconds", minimum=0, name=name),
        timeout_seconds=require_number(table, "timeout_seconds", minimum=0.001, name=name),
        max_retries=require_int(table, "max_retries", minimum=0, name=name),
        backoff_seconds=require_number(table, "backoff_seconds", minimum=0, name=name),
    )


def _model(table: dict[str, object]) -> ModelSettings:
    name = f"{_NAME}.model"
    return ModelSettings(
        name=require_str(table, "name", name).strip(),
        revision=require_str(table, "revision", name).strip(),
        max_length=require_int(table, "max_length", minimum=1, name=name),
        embedding_width=require_int(table, "embedding_width", minimum=1, name=name),
    )


def _fingerprint(table: dict[str, object]) -> FingerprintSettings:
    name = f"{_NAME}.fingerprint"
    return FingerprintSettings(
        radius=require_int(table, "radius", minimum=1, name=name),
        n_bits=require_int(table, "n_bits", minimum=1, name=name),
    )


def _columns(table: dict[str, object]) -> CatalogColumns:
    fields = CatalogColumns.__dataclass_fields__
    values = {key: require_str(table, key, f"{_NAME}.columns").strip() for key in fields}
    return CatalogColumns(**values)


def _tri_path(table: dict[str, object], name: str) -> str:
    path = require_str(table, "path", name).strip()
    if not path.startswith("/") or "{start}" not in path or "{end}" not in path:
        raise ValueError(f"{name}.path must start with / and contain {{start}} and {{end}}")
    return path


def _tri_list(table: dict[str, object]) -> TriListSettings:
    name = f"{_NAME}.tri_list"
    return TriListSettings(
        path=_tri_path(table, name),
        page_size=require_int(table, "page_size", minimum=1, name=name),
        cas_field=require_str(table, "cas_field", name).strip(),
        name_field=require_str(table, "name_field", name).strip(),
        inactive_field=require_str(table, "inactive_field", name).strip(),
        active_value=require_str(table, "active_value", name).strip(),
        keep_delisted=require_bool(table, "keep_delisted", name),
    )


def load_read_across_settings(path: Path | None = None) -> ReadAcrossSettings:
    """Load and validate the read-across settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), _NAME)
    return ReadAcrossSettings(
        directory=project_path(table, "directory", _NAME),
        file_template=_shard_template(table),
        prefix_digits=require_int(table, "prefix_digits", minimum=1, name=_NAME),
        alpha=require_fraction(table, "alpha", _NAME),
        min_hybrid_score=require_fraction(table, "min_hybrid_score", _NAME),
        pubchem=_pubchem(subtable(table, "pubchem", _NAME)),
        model=_model(subtable(table, "model", _NAME)),
        fingerprint=_fingerprint(subtable(table, "fingerprint", _NAME)),
        columns=_columns(subtable(table, "columns", _NAME)),
        tri_list=_tri_list(subtable(table, "tri_list", _NAME)),
    )


@lru_cache(maxsize=1)
def get_read_across_settings() -> ReadAcrossSettings:
    """Return the cached read-across settings from the default file."""
    return load_read_across_settings()
