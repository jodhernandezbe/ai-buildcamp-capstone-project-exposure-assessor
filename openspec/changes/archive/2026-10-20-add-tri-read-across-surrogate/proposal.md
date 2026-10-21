## Why

Many chemicals a user asks about are not on the TRI list or lack an inhalation toxicity
benchmark (RfC, IUR), so the assessment stops at "no usable value". EPA's Generalized
Read-Across (GenRA) practice fills that gap with the closest well-characterized analogue.
This change gives the agent a tool that names that analogue among TRI chemicals and says how
close it is and whether the match falls inside a stated applicability domain. The tool does
not invent a value.

## What Changes

- New agent tool `find_tri_read_across_surrogate` (in `tools/informatics/`). It takes a CAS
  number and returns either a direct TRI catalog match or the closest TRI surrogate. The
  result carries the MolDeBERTa cosine, ECFP4 Tanimoto and hybrid scores, the
  query/surrogate molecular-weight ratio, an applicability-domain flag and warnings. It has
  optional filters for chemicals with an IRIS benchmark and for a NAICS sector prefix.
- New pure similarity equations in `models/` (mean centering as an isotropy correction,
  vectorized cosine, vectorized Tanimoto, weighted hybrid score, best-match selection and the
  leave-one-out score distribution used to calibrate the threshold), with no I/O and no ML
  imports.
- New helpers in `tools/informatics/helpers/read_across/`:
  - a lazily loaded MolDeBERTa (`SaeedLab/MolDeBERTa-base-123M-mtr`) embedder, injected
    into the tool so tests use a fake;
  - RDKit canonicalization and Morgan ECFP4 bit vectors;
  - a PubChem PUG REST SMILES/MW lookup through the shared retrying `tools/http.py`;
  - a cached reader for the sharded TRI catalog.
- New offline builder `scripts/build_tri_embeddings.py`. It reads the current TRI chemical
  list from Envirofacts `tri_chem_info`, so a rerun picks up listing changes. It drops
  groups and placeholders (no valid CAS number: N-codes, `MIXTURE`, `TRD SECRT`, ...) and
  delisted chemicals. Each chemical reuses the SMILES already stored in the on-disk
  catalog, and only chemicals not on disk are resolved on PubChem. It then writes
  `data/tri_chemicals/`, one parquet shard per leading CAS digit (float32 vectors, zstd), which is committed. Shards keep every file under the repository's 1000 KB limit and make a rebuild rewrite only the shards that changed.
- New `[read_across]` section in `config/settings.toml` with a typed loader
  `config/read_across.py`. It holds the PubChem URL template, timeout and retry policy, the
  model name and max token length, the fingerprint radius and bit count, alpha (0.55), the
  applicability-domain threshold (0.60), the catalog path and columns, and the
  `tri_chem_info` path, page size, field names and delisting rule. The Envirofacts base URL
  and request policy stay the shared `[efservice]` ones.
- Dependencies added to `[project].dependencies`: `torch`, `transformers`, `rdkit`,
  `pandas`, `pyarrow`.
- The tool is registered in `tools/informatics/TOOLS` and `tools/registry.py`. Its
  description carries the decision guidance: when to use it, that the applicability-domain
  flag and score must be reported, and that a surrogate's benchmark is a read-across
  estimate, not a measured value for the query chemical. Matching phrases are pinned in
  `tests/tools/test_tool_descriptions.py`.
- `tools/CLAUDE.md` gains a second provider-import exception: only the MolDeBERTa helper
  imports `torch`/`transformers`.

## Capabilities

### New Capabilities
- `chemical-similarity-model`: pure vectorized cosine, Tanimoto and hybrid read-across
  scoring and best-candidate selection.
- `tri-read-across-tool`: the agent tool. It covers CAS validation, catalog filtering, the
  direct-match fast path, PubChem resolution, surrogate selection, the applicability domain,
  the MW ratio, and fail-closed warnings.
- `tri-read-across-catalog`: the offline builder of the TRI embedding catalog from
  Envirofacts, including group and delisting exclusions, on-disk SMILES reuse with a
  PubChem fallback, the sharded layout and the parquet schema.

### Modified Capabilities
- `app-configuration`: adds a "Read-across settings" requirement for the new `[read_across]`
  section, and adds the agent's sampling temperature (0) to "Agent chat model settings".
- `agent-system-prompt`: explains how an assessor treats a missing chemical (not identified,
  identified without data, absent from the inventory), states the CAS rule on its own, and
  gives the reply shape when the assessment cannot start.

## Impact

- Code: `models/` (new similarity module); `tools/informatics/` (tool and helpers);
  `tools/schemas.py` (`ReadAcrossMatch`); `tools/registry.py`; `config/` (loader and
  settings); `scripts/build_tri_embeddings.py`; mirrored tests under `tests/models/`,
  `tests/tools/informatics/`, `tests/config/` and `tests/scripts/`; `tools/CLAUDE.md`;
  README.
- Dependencies: torch, transformers, rdkit, pandas and pyarrow make `uv sync` much heavier.
  The about-123M-parameter model downloads from Hugging Face on the first real query (not in
  unit tests).
- Data: a new committed parquet in `data/` (a few MB). The SRS xlsx export is no longer used.
- Agent: one more bound tool. Eval cassettes may need re-recording if the agent starts
  calling it, so rerun `pytest -m eval` three times after the change.
- External services: PubChem PUG REST (no key) for query chemicals and for new catalog
  chemicals, and Envirofacts `tri_chem_info` (builder only). Both are time-bounded and
  retried.
