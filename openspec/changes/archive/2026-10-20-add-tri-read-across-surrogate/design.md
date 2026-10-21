## Context

See proposal.md (Why) for motivation. The original request specified a single
`tools/chemicals/read_across.py`, a hard-coded PubChem URL and `httpx.get`, and tests in
`tests/tools/test_read_across.py`. These conflict with the project rules: URLs and settings
live in `config/`, pure equations live in `models/`, helpers go in `<tool folder>/helpers/`,
tests mirror the package, functions are at most 18 lines, pyright runs in strict mode, and
data problems return `None` plus a warning. With the user's agreement, this design keeps the
requested behavior and places it to fit those rules.

The first live run against the real model then showed the specified similarity metric did not
rank analogues correctly; decisions 7 and 8 record that evidence and the correction.

## Goals / Non-Goals

**Goals:**
- The requested math, waterfall, defaults (alpha 0.55, threshold 0.60, ECFP4 radius 2 with
  1024 bits, mean-pooled MolDeBERTa with max length 128) and result fields, plus `warnings`.
- Unit tests that need neither network nor model download nor GPU.
- One committed catalog built from the live TRI chemical list, cheap to rebuild.

**Non-Goals:**
- Applying the MW factor to RfC/IUR, or fetching the surrogate's benchmarks. The agent
  chains `fetch_chemical_properties` on the surrogate CAS itself.
- Producing the `has_iris_benchmark` or `naics_prefixes` columns. The filters are honored
  when those columns exist; populating them is a later change.
- Top-k surrogates, GenRA-style activity prediction, or an AD computed from local density.

## Decisions

1. **Layout.**
   - `models/chemistry/similarity.py`: cosine, Tanimoto, hybrid and best index. These are
     pure NumPy functions validated with `ValueError`; scores are dimensionless, and the
     docstrings say so.
   - `tools/informatics/read_across.py`: the `@tool` and its waterfall.
   - `tools/informatics/helpers/read_across/`, split by concern:
     - `structure.py`: RDKit canonicalization, InChI to SMILES, ECFP4 bits, MolWt;
     - `moldeberta.py`: the embedder;
     - `pubchem.py`: SMILES and MW lookup;
     - `catalog.py`: parquet load and validation, plus the filters;
     - `tri_list.py`: reads and pages `tri_chem_info` and returns the discrete, listed
       chemicals (builder only).

   *Alternative:* one module, as requested. Rejected because it breaks the 18-line limit,
   the layering and test mirroring.
2. **Embedder injection.** A `SmilesEmbedder` Protocol (`(smiles: str) -> NDArray[float32]`)
   is passed into a plain `find_surrogate(...)` core. The `@tool` wrapper builds the default
   at the outer edge: `moldeberta.default_embedder()`. That embedder sits behind
   `@lru_cache(maxsize=1)`, picks the device in the order mps, then cuda, then cpu, calls
   `eval()`, and uses `no_grad`, attention-mask mean pooling and L2 normalization. Only
   `moldeberta.py` imports `torch`/`transformers`, and it imports them lazily. That
   exception is recorded in `tools/CLAUDE.md`.

   Tests pass a fake embedder that returns deterministic synthetic vectors, so no
   `_load_moldeberta` patching is needed. The requested mocking still holds: PubChem is
   faked through an injected `RetryingClient`.
3. **HTTP.** PubChem goes through the existing `tools/http.RetryingClient`, which handles
   timeout, throttling, retries and `Retry-After`. Its policy comes from
   `[read_across.pubchem]`. The fixed `timeout=20.0` from the request becomes the
   configured default. `HttpRequestError`, a 404 and a malformed body all become `None`
   plus a warning.
4. **Fail closed, not raise.** `ReadAcrossMatch` (in `tools/schemas.py`) keeps every
   requested key, but makes the query/surrogate SMILES, MW, scores and scaling factor
   `| None` and adds `warnings: list[str]`. An invalid CAS, an unresolved structure or a
   missing MW returns a full result with Nones. A missing or malformed catalog raises,
   because that is a setup error. CAS validation reuses `commons.cas.format_cas`, which goes
   beyond the requested whitespace strip.
5. **Catalog source.** The builder reads Envirofacts `tri_chem_info` (fields
   `cas_registry_number`, `chem_name` and `inactive_date`) through `tools/http.RetryingClient`,
   using the shared `[efservice]` base URL and policy. The path
   `tri_chem_info/rows/{start}:{end}/JSON` and the page size of 2000 live in
   `[read_across]`.
   - **Paging:** in October 2026 the list was 860 rows, one page; a full page triggers the
     next request.
   - **Groups and placeholders:** a row is one when its CAS field fails `format_cas`. On
     that date this covered 38 rows: 36 N-codes plus `MIXTURE`, `TRD SECRT`, `NA` and
     `INVALID`. No separate group flag is needed.
   - **Delisted chemicals:** an `inactive_date` other than "9999" means delisted (21 rows);
     these are dropped by default.

   The SRS xlsx export is dropped, because it would go stale. *Alternative:* the SRS export,
   which ships SMILES and InChI. Rejected because it is a dated manual download.
6. **The on-disk catalog is the structure cache.** Before resolving, the builder loads the
   existing parquet (if any) into a CAS to SMILES and MW map.
   - **Reuse:** chemicals in the map reuse their SMILES and MW.
   - **New chemicals:** only chemicals missing from the map go to PubChem, through the same
     `pubchem.py` helper the tool uses. That is about 820 requests on a first build at the
     configured delay, and only new listings on later builds.
   - **Molecular weight:** for new chemicals, MW comes from RDKit `Descriptors.MolWt` on
     the resolved structure (average MW, the same basis as PubChem `MolecularWeight`), so
     catalog MWs are consistent.
   - **Embeddings:** these and fingerprints are recomputed for every row on every build.
     That is about a minute on CPU, and it means a model or settings change can never
     leave stale vectors.
   - **Salts:** multi-fragment structures are kept as given.
   - **Safe write:** every shard is staged beside its target and all are renamed together at
     the end, so a failed build never corrupts the committed catalog.
   - **Sharded, compact storage.** One parquet file with float64 vectors and int64 bits was
     3.6 MB, over the repository's 1000 KB large-file hook, and every other committed data
     file is under 400 KB. Two changes fix it without touching the hook:
     - *Compact types:* float32 vectors and int8 bits with zstd (the model emits float32
       anyway, and the bits are 0/1) give 2.6 MB in one file. float16 would reach 1.1 MB but
       still miss the limit and would perturb cosines, so it was rejected.
     - *Shards by leading CAS digit,* the scheme `data/nei_stacks/` already uses
       (`directory`, `file_template`, `prefix_digits` in `[read_across]`): nine files, the
       largest 891 KB (digit 1, 198 chemicals), 3.1 MB in total. Rows are sorted by CAS inside
       each shard.
     - *Why shard, beyond the size limit:* the pinned model re-embeds a SMILES to identical
       bytes, so adding a chemical rewrites only its own shard (about 0.1-0.9 MB of git
       history instead of 2.6 MB). Reads are unchanged: scoring needs every chemical, so every
       shard is read on load, unlike `nei_stacks`, which reads one shard per lookup.
     - *Byte-stability needed one fix:* RDKit sums atomic masses in atom order, so the same
       molecule parsed from PubChem's SMILES and from its canonical SMILES differed by about
       1e-13 g/mol, which changed 281 of 712 stored weights on the first rebuild. The weight
       is now rounded to 4 decimals (finer than the atomic masses), after which two
       back-to-back rebuilds are byte-identical.
     - *Rebuild cost* with the shards present: about 60 s (21 s model load, 8 s to embed 712
       SMILES, one Envirofacts request, no PubChem). From scratch it is about 4 minutes and
       roughly 800 PubChem requests, so committing the shards is what makes a fresh clone
       usable at once.
     - *Alternatives rejected:* gitignore the catalog like the SCC vector index (every clone
       pays the slow path); raise the hook limit (weakens the guard for every file and adds
       2.6 MB to history per rebuild); store structures only and embed on load (needs the model
       and about a minute at every start).
7. **Isotropy correction (mean centering), added after the first live run.** The method as
   first specified used the model's raw cosine. Measured against the committed 712-chemical
   catalog, that does not work:
   - MolDeBERTa's vectors sit in a narrow cone (representation anisotropy, the "cone
     effect"), so raw pairwise cosines are compressed into about [0.424, 1.0]. The lowest
     raw cosine between *any* two TRI chemicals is 0.424.
   - Isohexane (107-83-5) then misranks: sec-butyl alcohol scores 0.982 and comes first,
     ahead of n-hexane, the structural analogue the spec's own worked example expects.
   - The applicability domain barely rejects anything: 94.7% of catalog chemicals have a
     nearest neighbour at or above 0.60, and caffeine (58-08-2) is admitted as in-domain
     with methazole, a herbicide, as its surrogate.

   Subtracting the catalog mean embedding mu = (1/N) * sum(e_i) before L2 normalizing (a
   first-order isotropy correction) fixes both, measured on the same catalog:
   - isohexane ranks n-hexane first; the homologue heptane -> n-hexane stays high at 0.938;
     an identical structure still scores exactly 1.0;
   - caffeine falls to 0.379 and is rejected as out of domain;
   - the leave-one-out in-domain share settles at 66%, so the check discriminates.

   *Alternatives considered:* raising the threshold alone (rejected: it cannot fix the
   *ranking*, which is what sent isohexane to an alcohol); dropping the embedding and using
   the fingerprint alone (rejected: it loses the learned chemistry the embedding contributes,
   and the request specifies a hybrid); whitening or all-but-the-top (rejected for now: more
   parameters to fit and to store, for a problem first-order centering already solves).

   Consequences:
   - mu is derived from the **whole** catalog when it is loaded and cached with it; the
     filters narrow which chemicals can be chosen but never change a pair's score.
   - The catalog keeps storing **uncentered** vectors, so this needs no rebuild and the
     correction can change later without one.
   - A centred cosine is relative to the catalog distribution, so a score is only comparable
     within one catalog version. The tool must not present scores across versions as
     equivalent.
   - A query whose embedding equals mu has no direction once centred; that is a data problem,
     so it returns no surrogate plus a warning.
8. **Threshold calibration.** `min_hybrid_score` stays **0.60**, now because the centred
   leave-one-out distribution puts it at the 33rd-34th percentile (p33 = 0.597, p34 = 0.601;
   median 0.687, p5 = 0.392), so it rejects the third of the catalog whose nearest TRI
   neighbour is weakest and admits the rest. Caffeine's 0.379 sits near p4. The calibration is
   recorded next to the value in `settings.toml`, and `models/chemistry/similarity.py` exposes
   the leave-one-out distribution so it can be recomputed when the catalog or the model
   changes.

   What this calibration does **not** fix, measured on the same catalog:
   - Isohexane ranks n-hexane first but scores 0.554, so it is itself reported as *outside*
     the domain. ECFP4 rates a branched isomer as only modestly similar (Tanimoto 0.286)
     even though the two are both C6H14.
   - Neohexane (2,2-dimethylbutane, also C6H14) still misranks: it picks Cumene, an
     aromatic, over n-hexane at 0.456. Centering did not fix branched isomers.
   - No alpha/threshold pair tested separates genuine analogues from unrelated chemicals
     cleanly. Raising alpha to 0.70 brings isohexane in at 0.627 but also admits water
     (0.659) and elemental carbon (0.619), which is worse than rejecting isohexane.

   So the tool is calibrated to **fail closed**: alpha stays 0.55 and the threshold 0.60, the
   ranking is the tool's real contribution, and a conservative domain flag is preferred over a
   permissive one. The two component scores are always reported so a reader can see whether
   the embedding or the fingerprint carried the match. An exact molecular-formula (isomer)
   rule would address both cases honestly and is the obvious next step, deliberately left out
   of this change.

9. **Fast vectorized search.** At load, the catalog becomes a float32 `(N, 768)` matrix and
   a uint8 `(N, 1024)` matrix, cached once per process. The loader also computes the mean
   embedding once and stores both it and the centred, re-normalized embedding matrix on the
   catalog, so a query centres against a cached vector and scoring stays one matrix product.
   The loader returns read-only views or copies, never mutable cached arrays. Filters apply a
   boolean mask to both matrices and carry the mean vector through unchanged.
10. **Typing.** rdkit, transformers and pandas have partial stubs. Each untyped call stays
   inside the helper that owns it and is wrapped with explicit `cast` to typed NumPy
   results, so pyright strict stays clean without file-wide ignores.
11. **Tests mirror the layout.**
   - `tests/models/chemistry/test_similarity.py`, including centering (unit length, the
     shared component removed, a vector at the centre) and the leave-one-out distribution;
   - `tests/tools/informatics/test_read_across.py`: a 3-chemical parquet in `tmp_path`
     (hexane, benzene, TCE), with the direct path, isohexane to hexane, out of domain,
     filters not moving the scores, a query at the catalog centre, and failures;
   - `tests/tools/informatics/helpers/read_across/test_*.py`;
   - `tests/config/test_read_across_settings.py`;
   - `tests/scripts/test_build_tri_embeddings.py`;
   - a `tests/smoke/` live test (marked `smoke`) that runs PubChem and the real model, and
     pins what the first live run exposed: isohexane -> n-hexane, and caffeine rejected as
     out of domain. These are the regression guard for the isotropy correction.

   RDKit runs for real in the unit tests; it is fast and deterministic. Fixture embeddings
   are obviously synthetic (unit basis vectors), never values that look like real model
   output.

12. **The name-only regression was unclear instructions, not the tool.** Registering the tool
    made `chemical-name-only` fail about half the time: given only "formaldehyde", the agent
    called a tool with the recalled CAS 50-00-0 or wrote it in its reply. Traces showed the
    surrogate tool was never called; the failure was the very first model turn. Measured on
    that first turn (30 samples per condition, temperature 0):
    - current prompt: 30/30 clean without the tool, 8-16/30 with it; neutral dummy tools,
      including one taking a `cas_number`, stayed clean, so the tool count was not the cause.
    - rewording only the tool description did not help (2/30); no single sentence was the
      trigger, and removing two harmless mentions of another tool flipped it to 0/30.
    - the cause was the prompt: the CAS rule was a clause inside "ask if no tool can supply
      it", the prompt never said what an assessor does when a chemical is missing in its
      different senses, and the output format only described a full report, which the model
      filled ("Summary: ... formaldehyde (CAS 50-00-0)").
    - with the clarified prompt: 30/30 in five independent batches, with or without the tool.

    The clarified prompt explains the three ways a chemical can be missing, states the CAS
    rule on its own, and gives the reply shape when the assessment cannot start. The tool
    description now opens with its precondition (a CAS the user gave; never identifies a
    chemical from a name) instead of reading as a sequence of calls.

    The wording is fragile: a paraphrase of the same rule ("ask for the CAS number and make
    that your whole reply") fell to 12/30. The measured wording is therefore pinned by the
    prompt test, so a later edit must be re-measured. *Alternative considered:* a code guard
    rejecting tool calls whose CAS does not appear in the conversation. It blocks the harm
    deterministically but not an attempted call or a CAS written in the reply, so it is left
    as optional defence in depth.
13. **Temperature 0.** The agent sampled at the provider default (1.0). `[agent].temperature`
    is now 0: the baseline became fully clean, and a screening assessment should be
    reproducible. It is not fully deterministic for gpt-4.1 (batches of the same input still
    differ), and it did not by itself fix the regression above (14/30 vs 16/30).

## Risks / Trade-offs

- [torch/transformers are heavy in main deps (the user's choice)] → `uv sync` and CI get
  slower. Imports stay lazy, so tool import and unit tests don't load torch. `pip-audit`
  covers the new deps.
- [The model downloads at first real call, about 500 MB] → Document it in the README; the
  smoke test pre-warms it. An offline machine gets a raised setup error, not a silent bad
  score.
- [The ECFP4 Tanimoto for branched vs linear isomers is modest] → The AD threshold is
  configurable, and the result always shows both component scores.
- [The applicability domain is a single global threshold] → Calibrated against the catalog's
  leave-one-out distribution (decision 8) rather than guessed; the description tells the agent
  to report the score and flag, and to treat read-across as a screening estimate.
- [A centred score depends on the catalog, so rebuilding it shifts scores slightly] → The
  mean moves little when a few chemicals are added, but scores are documented as comparable
  only within one catalog version, and the smoke test pins the behaviour that matters
  (isohexane in domain, caffeine out) after any rebuild.
- [The domain flag rejects some sound analogues, such as isohexane at 0.554] → Accepted
  deliberately: fail closed, report the ranking and both component scores, and document it.
  Loosening the threshold admits water and elemental carbon, a worse failure.
- [Centering is a first-order correction, not a cure for anisotropy] → The leave-one-out
  distribution is exposed so the threshold can be recalibrated, and the result always carries
  both component scores so a reader can see whether the embedding or the fingerprint drove
  the match.
- [A new tool may change agent trajectories] → Rerun `pytest -m eval` three times and
  re-record cassettes if the tool is called.
- [The Envirofacts schema could drift or a field could be renamed] → The builder validates
  the configured fields on the first page and fails before writing, so the committed
  catalog stays intact.
- [The first build makes about 820 PubChem requests] → Throttled at the configured delay
  (about 4 minutes). It happens only without the committed shards; later builds query only
  new listings and take about a minute.
- [A delisted chemical may be the best structural analogue] → It is dropped by default, and
  a config flag keeps delisted chemicals.

## Migration Plan

Additive. Steps: `uv sync`, run `uv run python -m scripts.build_tri_embeddings` (the first
build resolves every chemical on PubChem), and commit the shards in `data/tri_chemicals/`. The SRS xlsx in `data/`
is not used. To roll back,
remove the tool from `TOOLS`; nothing else depends on it.
