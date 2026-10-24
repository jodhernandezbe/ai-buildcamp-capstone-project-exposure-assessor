"""Test doubles for read-across: an HTTP fake, a fake embedder and a small catalog writer.

Embeddings are unit basis vectors (obviously synthetic, never model output). Structures,
fingerprints and molecular weights are computed by RDKit from real SMILES.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path

import httpx
import numpy as np
from numpy.typing import NDArray

from config.read_across import ReadAcrossSettings, load_read_across_settings
from config.tri_categories import load_tri_categories_settings
from tools.http import RetryingClient
from tools.informatics.helpers.read_across.catalog import write_columns
from tools.informatics.helpers.read_across.structure import describe
from tools.tri_categories import CategoryIndex, load_index

WIDTH = 768

HEXANE = ("110-54-3", "n-Hexane", "CCCCCC")
BENZENE = ("71-43-2", "Benzene", "c1ccccc1")
TCE = ("79-01-6", "Trichloroethylene", "ClC=C(Cl)Cl")
CHEMICALS = (HEXANE, BENZENE, TCE)


def unit(index: int, width: int = WIDTH) -> NDArray[np.float32]:
    """The ``index``-th unit basis vector."""
    vector = np.zeros(width, dtype=np.float32)
    vector[index] = 1.0
    return vector


def settings(tmp_path: Path, **changes: object) -> ReadAcrossSettings:
    """The shipped settings, with the catalog shards in ``tmp_path`` and any other changes."""
    base = load_read_across_settings()
    return replace(base, directory=tmp_path / "catalog", **changes)  # type: ignore[arg-type]


def canonical(smiles: str, s: ReadAcrossSettings) -> str:
    found = describe(smiles, s.fingerprint)
    assert found is not None
    return found.smiles


@dataclass
class FakeEmbedder:
    """Returns a fixed vector per canonical SMILES and records what it embedded."""

    vectors: Mapping[str, NDArray[np.float32]]
    calls: list[str]

    def __call__(self, smiles: str) -> NDArray[np.float32]:
        self.calls.append(smiles)
        return self.vectors[smiles]


def embedder(s: ReadAcrossSettings, by_smiles: Mapping[str, NDArray[np.float32]]) -> FakeEmbedder:
    """A fake embedder keyed by any SMILES spelling (canonicalized here)."""
    return FakeEmbedder({canonical(k, s): v for k, v in by_smiles.items()}, [])


def catalog_columns(
    s: ReadAcrossSettings,
    chemicals: tuple[tuple[str, str, str], ...] = CHEMICALS,
    extra: Mapping[str, list[object]] | None = None,
) -> dict[str, list[object]]:
    """Catalog columns for ``chemicals``, embedding row ``i`` as ``unit(i)``."""
    found = [describe(smiles, s.fingerprint) for _, _, smiles in chemicals]
    assert all(f is not None for f in found)
    c = s.columns
    return {
        c.cas: [cas for cas, _, _ in chemicals],
        c.name: [name for _, name, _ in chemicals],
        c.smiles: [f.smiles for f in found if f],
        c.molecular_weight: [f.molecular_weight for f in found if f],
        c.embedding: [unit(i, s.model.embedding_width).tolist() for i in range(len(chemicals))],
        c.bits: [f.bits.tolist() for f in found if f],
        **(extra or {}),
    }


def write_catalog(s: ReadAcrossSettings, columns: Mapping[str, list[object]]) -> tuple[Path, ...]:
    """Write the columns as shards grouped by CAS prefix, the way the builder does."""
    s.directory.mkdir(parents=True, exist_ok=True)
    cas = [str(c) for c in columns[s.columns.cas]]
    written: list[Path] = []
    for prefix in sorted({s.shard_prefix(c) for c in cas}):
        rows = [i for i, c in enumerate(cas) if s.shard_prefix(c) == prefix]
        shard = {name: [values[i] for i in rows] for name, values in columns.items()}
        path = s.shard_path(prefix)
        write_columns(shard, path, s.columns)
        written.append(path)
    return tuple(written)


Handler = Callable[[httpx.Request], httpx.Response]


class Server:
    """An HTTP fake: answers with ``handler`` and records every request URL."""

    def __init__(self, handler: Handler) -> None:
        self.urls: list[str] = []

        def record(request: httpx.Request) -> httpx.Response:
            self.urls.append(str(request.url))
            return handler(request)

        http = httpx.Client(transport=httpx.MockTransport(record))
        self.client = RetryingClient(load_read_across_settings().pubchem, http, lambda _: None)


def pubchem_body(**properties: object) -> dict[str, object]:
    return {"PropertyTable": {"Properties": [{"CID": 1, **properties}]}}


def answer(body: object, status: int = 200) -> Handler:
    return lambda request: httpx.Response(status, json=body)


def no_network(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"unexpected request to {request.url}")


CATEGORY_HEADER = "CAS NUMBER,CATEGORY CODE,CATEGORY NAME,CHEMICAL NAME,CHEMICAL TYPE,SOURCE"


def category_index(tmp_path: Path, *rows: str) -> CategoryIndex:
    """A category index read from ``rows`` (CSV lines, the shipped column order)."""
    path = tmp_path / "categories.csv"
    path.write_text("\n".join([CATEGORY_HEADER, *rows]) + "\n", encoding="utf-8")
    return load_index(replace(load_tri_categories_settings(), path=path))
