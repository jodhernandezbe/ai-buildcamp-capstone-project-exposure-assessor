## 1. Setup

- [x] 1.1 Add `torch`, `transformers`, `rdkit`, `pandas` and `pyarrow` to `[project].dependencies`; run `uv sync`; confirm `pip-audit` is clean
- [x] 1.2 Leave the untracked SRS xlsx out of the change (not used, not committed)
- [x] 1.3 Add a `[read_across]` section to `config/settings.toml`: the PubChem URL template with `{cas}` and its request policy; the model name, max length 128 and width 768; fingerprint radius 2 and 1024 bits; alpha 0.55 and threshold 0.60; the catalog path and columns; the `tri_chem_info/rows/{start}:{end}/JSON` path, page size 2000, field names (`cas_registry_number`, `chem_name`, `inactive_date`), active value "9999", and `keep_delisted = false`
- [x] 1.4 Implement `config/read_across.py` (typed frozen dataclass and loader with `lru_cache`, validators from `config/parsing.py`); write `tests/config/test_read_across_settings.py` covering the loaded values and each invalid-entry `ValueError`

## 2. Similarity model

- [x] 2.1 Create `models/chemistry/__init__.py` and `models/chemistry/similarity.py` with the vectorized cosine (clipped), Tanimoto (union floored at 1e-9), hybrid score and best index (lowest index on ties). Validate inputs with `ValueError` and state in docstrings that scores are dimensionless
- [x] 2.2 Write `tests/models/chemistry/test_similarity.py`: identical gives 1.0, orthogonal or disjoint gives 0.0, empty fingerprints give 0.0, clipping above 1, the weighted blend, and negative tests for width mismatch, non-binary entries, bad alpha, NaN and empty catalog

## 3. Read-across helpers

- [x] 3.1 Add `ReadAcrossMatch` to `tools/schemas.py`: all requested fields, with nullable values, plus `warnings`
- [x] 3.2 `tools/informatics/helpers/read_across/structure.py`: canonical SMILES, ECFP4 uint8 bits through `rdFingerprintGenerator`, and MolWt. A parse failure returns `None`. Typed casts wrap the RDKit calls
- [x] 3.3 `tools/informatics/helpers/read_across/pubchem.py`: look up SMILES and MW through an injected `RetryingClient`, taking the SMILES from the first of the Canonical, Isomeric and Connectivity properties; a failure or malformed body returns `None` plus a reason
- [x] 3.4 `tools/informatics/helpers/read_across/moldeberta.py`: the `SmilesEmbedder` Protocol and a lazy `default_embedder()` with `lru_cache`, device order mps, cuda, cpu, `eval()`, `no_grad`, masked mean pooling and L2 normalization. This is the only module that imports torch/transformers
- [x] 3.5 `tools/informatics/helpers/read_across/catalog.py`: load every parquet shard once, validate columns and widths (raise on a setup error), build the float32 and uint8 matrices, return read-only arrays, and apply the benchmark and NAICS filters with fallback and warnings
- [x] 3.6 `tools/informatics/helpers/read_across/tri_list.py`: page `tri_chem_info` through an injected `RetryingClient` built with the shared `[efservice]` base URL and policy, request the next page while a page is full, and validate the configured fields (raise on drift). Keep rows whose CAS passes `format_cas`, drop delisted rows unless `keep_delisted` is set, de-duplicate CAS numbers, and return the kept chemicals plus drop counts by reason
- [x] 3.7 Write mirrored tests under `tests/tools/informatics/helpers/read_across/` (with `__init__.py` files): structure parsing and bits; PubChem alias, failure and malformed cases with a fake client; catalog validation errors and filters; TRI list paging, group codes (N420, MIXTURE, TRD SECRT), delisted rows, duplicates and field drift; device selection and pooling with stubbed torch objects

## 4. Tool

- [x] 4.1 `tools/informatics/read_across.py`: the core `find_surrogate(cas, *, catalog, embedder, client, settings, filters)` waterfall (validate CAS with `format_cas`, filter, direct fast path, PubChem, score, applicability domain, MW factor, warnings), plus the `@tool find_tri_read_across_surrogate` wrapper that builds defaults at the edge. Its description holds the decision guidance from the spec
- [x] 4.2 Register the tool in `tools/informatics/__init__.py` `TOOLS`; update `tests/tools/test_registry.py`, and pin the description phrases in `tests/tools/test_tool_descriptions.py`
- [x] 4.3 Write `tests/tools/informatics/test_read_across.py` with a `tmp_path` 3-chemical parquet (110-54-3, 71-43-2, 79-01-6) and a fake embedder and client. Cover: the direct match with no HTTP call; 107-83-5 to 110-54-3 with factor 1.0 and the AD flag; out of domain below 0.60; exactly at the threshold; invalid CAS; PubChem failure; missing MW; each filter with its fallback; a missing catalog raising
- [x] 4.4 Update `tools/CLAUDE.md` with the provider-import exception for `moldeberta.py`, and add a README section on the tool, the model download and the catalog rebuild

## 5. Catalog builder

- [x] 5.1 `scripts/build_tri_embeddings.py`: argparse `--directory`, with the default from config. Fetch the kept chemicals with `tri_list.py`, load the existing parquet (if any) as a CAS to SMILES and MW map, reuse on-disk structures, and resolve only missing chemicals on PubChem (throttled) with RDKit MW. Recompute the embedding and bits for every row, write to a temporary file and rename it over the catalog, and print a drop report. Exit non-zero, without writing, on an Envirofacts failure
- [x] 5.2 Write `tests/scripts/test_build_tri_embeddings.py` with fake Envirofacts and PubChem clients and a fake embedder. Cover: a group code and a delisted row are dropped; a chemical on disk is reused with no PubChem call; a new chemical is resolved on PubChem; a first build with no catalog; an unresolvable chemical is reported; a chemical no longer listed is removed; an Envirofacts failure leaves the existing file unchanged; the written parquet round-trips through the tool's catalog loader
- [x] 5.3 Run the builder against live Envirofacts and PubChem, review the drop report (21 delisted, 38 groups, 89 unresolved on PubChem), and commit the shards in `data/tri_chemicals/`

## 6. Isotropy correction and threshold calibration

Added after the first live run exposed the raw cosine misranking analogues (design decisions 7
and 8). The catalog file does not need rebuilding: it keeps storing uncentered vectors.

- [x] 6.1 Add to `models/chemistry/similarity.py`: `mean_vector` (arithmetic mean of a matrix's rows), `centered` (subtract the mean, then L2-normalize, for a vector or a matrix; raise `ValueError` on a zero-length result, a width mismatch or a non-finite value) and `leave_one_out_scores` (each row's best hybrid score against the others; `ValueError` below two rows). State in the docstrings that scores are dimensionless and that a centred cosine is relative to the reference distribution
- [x] 6.2 Extend `tests/models/chemistry/test_similarity.py`: centred vectors are unit length, the component shared with the mean drops out, identical vectors still score 1.0, a vector at the centre raises, the mean of a two-row matrix, and the leave-one-out cases (duplicate rows score 1.0, a one-row catalog raises)
- [x] 6.3 In `tools/informatics/helpers/read_across/catalog.py`: compute the mean embedding from the full catalog on load, store it and the centred embedding matrix (read-only) on `Catalog`, and carry the mean unchanged through `subset`, so a filter never changes a score
- [x] 6.4 In `tools/informatics/read_across.py`: centre the query embedding on the catalog's mean before the cosine; a query at the centre returns no surrogate plus a warning (never raises)
- [x] 6.5 Update `tests/tools/informatics/test_read_across.py` and `test_catalog.py`: filters do not move the reported scores, a query embedding equal to the catalog mean is unresolved with a warning, and the existing direct-match and out-of-domain cases still hold
- [x] 6.6 Record the calibration in `config/settings.toml` beside `min_hybrid_score` (keep 0.60: centred leave-one-out p33 = 0.597, p34 = 0.601, median 0.687, in-domain share 66%), and note in the README that a score is comparable only within one catalog version

## 7. Sharded storage

Added when the single 3.6 MB catalog file tripped the 1000 KB large-file hook (design decision 6).

- [x] 7.1 Store the catalog as one parquet shard per leading CAS digit (`directory`, `file_template`, `prefix_digits` in `[read_across]`), float32 vectors and int8 bits, zstd; the loader reads every shard as one catalog and rejects shards with different columns
- [x] 7.2 Builder: group rows by CAS prefix (sorted by CAS), stage every shard and rename them together, remove a shard whose digit has no chemical, reuse SMILES from all existing shards
- [x] 7.3 Round the stored molecular weight to 4 decimals so rebuilds are byte-identical regardless of SMILES spelling; verify two back-to-back live rebuilds give identical shards (done: 9/9 identical)
- [x] 7.4 Tests: shard layout and compact types, other shards untouched when one chemical is added, a failed build leaves the shards alone, shard disagreement, spelling-independent weight

## 8. Name-only regression (design decisions 12 and 13)

- [x] 8.1 Trace the failing runs message by message, and isolate the cause on the first turn: baseline vs read-across vs neutral dummy tools, tool position, description ablations, prompt variants (30 samples per condition)
- [x] 8.2 Add `[agent].temperature` (0, validated 0-2) through the chat model factory, with tests and the modified "Agent chat model settings" requirement
- [x] 8.3 Clarify `prompts/agent_system.md`: how an assessor treats a missing chemical, the CAS rule as its own instruction, the reply shape when the assessment cannot start; pin the measured wording in the prompt test
- [x] 8.4 Rewrite the read-across description to open with its precondition and drop the call-sequence wording; update its pinned phrases

## 9. Verification

- [x] 9.1 Extend the `tests/smoke/` live test (marked `smoke`) and run it: isohexane 107-83-5 ranks n-hexane 110-54-3 first, the homologue n-heptane 142-82-5 is in domain, caffeine 58-08-2 is out of domain and scores below isohexane, a listed chemical is a direct match, an unknown CAS warns. Isohexane's own score (0.554) sits below the 0.60 threshold, so it is reported out of domain; the limitation is documented in `design.md` and the README instead of loosening the threshold
- [x] 9.2 Run `uv run pytest`, `ruff format`, `ruff check`, `pyright`, `bandit`, the function-length check and `uv run pre-commit run --all-files`; all pass
- [x] 9.3 With the user's go-ahead (paid OpenAI calls), run `uv run pytest -m eval` three times: 12/12 passed in all three runs (chemical-name-only and full-assessment-with-nei-stacks), after the prompt clarification of group 8; no cassette needed re-recording
