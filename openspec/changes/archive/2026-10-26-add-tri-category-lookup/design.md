## Context

The read-across tool (`tools/informatics/read_across.py`) has two outcomes today: a direct
catalog hit (a discrete TRI chemical) or a hybrid-score surrogate. The catalog builder drops
every TRI group code (N420, N100, ...) because they are not CAS numbers, so a chemical that
TRI covers only through a category is treated as "not in TRI" and sent to similarity search.
The emissions tool queries Envirofacts with `cas_registry_number/{casrn}`; Envirofacts
stores category releases under the code (N420), so a member's own CAS finds nothing.

`data/chemicals_in_tri_categories.csv` has 2,693 rows (CAS NUMBER, CATEGORY CODE, CATEGORY
NAME, CHEMICAL NAME, CHEMICAL TYPE, SOURCE). Observed: no empty CAS; some CAS repeat across
categories (e.g. copper cyanides under copper and cyanide); a few category codes are CAS
numbers without hyphens (1336363 PCBs, 1330207 xylenes, 1332214 asbestos, ...); names contain
typos ("4-chloroplienol"), so the CAS number is the only key; ~half the rows are inorganic.

## Goals / Non-Goals

**Goals:**
- Order of resolution: discrete TRI chemical, then category member, then read-across.
- A category match is always visible to the user, with what it does and does not mean.
- Category members enlarge the read-across candidate set.

**Non-Goals:**
- Splitting a category's releases among its members (TRI does not report them that way).
- Borrowing a toxicity benchmark from a category; the chemical's own CAS keeps its own lookup.
- Identifying a chemical from its name, or repairing CAS numbers from names.
- Embedding inorganic members (metals, salts).

## Decisions

1. **A separate category module, not a catalog row.** The membership lookup is an exact CAS
   match on a small in-memory index built once from the CSV (frozen dataclass, tuples, copies
   returned), in `tools/informatics/helpers/category/`. Alternative: put members in the
   parquet catalog and test `is_direct`. Rejected: membership is exact and needs no embedding,
   it must also cover inorganics, and the catalog should stay "things scored by similarity".
   Path and column names go in `config/` (`[tri_categories]`), with a typed loader.

2. **Order in `find_surrogate`: catalog hit, category, similarity.** The category step sits
   between them and runs before PubChem. The chemical's structure and MW are looked up
   best-effort only to fill fields; failure leaves them None with a warning and does not change
   the resolution (fail closed on identity, not on decoration). Alternative: category before
   catalog. Rejected: a discrete TRI chemical has its own CAS releases; a category would
   aggregate them with others.

3. **Result gets `query_categories` and `surrogate_category`.** `ReadAcrossMatch` in
   `tools/schemas.py` gains two small TypedDict-typed fields (a list of `{code, name}`, and one
   `{code, name}` or None). A new `resolution_method` value "tri_category_member" keeps
   consumers' switch explicit. `within_applicability_domain` is true for a category member
   (membership is a regulatory fact, not an estimate) and the similarity fields are None, which
   keeps "no number invented" intact. The disclosure sentence lives in `warnings`, which the
   prompt already tells the model to relay.

4. **Emissions accept a category code.** The identifier check becomes: valid CAS, or a code in
   the category index. Numeric-style codes are normalised to hyphenated CAS when the CSV is
   loaded, so PCBs go through the CAS path unchanged. A category-code result carries a `note`
   that the releases are for the whole category. Alternative: a second tool. Rejected: one
   concept (releases), and the batch assessment would need to learn a new tool. The batch tool
   passes through the identifier it is given; the agent chooses the code from the read-across
   result (documented in tool descriptions, per the existing "descriptions carry decisions"
   rule).

5. **Only organic members become read-across candidates.** MolDeBERTa and ECFP4 describe
   organic structures; a Morgan fingerprint of "Cr(+3) salt" fragments is noise and would pull
   queries toward metals. Inorganic members stay reachable through step 2. Each added row
   carries `catalog_source` ("tri_list" or "tri_category") and `category_codes`/`category_names`
   (optional columns, like `naics_prefixes`; the loader tolerates their absence in old shards).
   A CAS already a discrete TRI chemical stays a TRI-list row. Builder reports the counts.

6. **Recalibrate, don't reuse, the domain threshold.** Adding ~1,000 organics changes the
   leave-one-out nearest-neighbour distribution (more neighbours raise scores). `min_hybrid_score`
   was set at p33 of the 712-chemical catalog; it is recomputed with
   `leave_one_out_scores` on the new catalog and recorded, also reporting TRI-list-only rows so
   the shift is visible. Scores stay comparable only within one catalog version (existing rule).

7. **Prompt change is reasoning, not procedure.** One paragraph in the missing-chemical
   section: a category can stand in, say so, releases are for the whole category, the benchmark
   still has to be the chemical's own. No tool names. Detail on reading the fields goes in the
   tool descriptions.

## Risks / Trade-offs

- [Category releases overstate one member] -> mandatory disclosure in tool result note, in the
  tool description and in the prompt; labelled an upper bound. Mass basis differs for metal
  compounds (TRI reports the metal portion); the note says "as reported under the category".
- [Group tracking of a member that is also reported by its own CAS] -> catalog hit wins (design 2).
- [CSV typos / bad CAS] -> rows with invalid CAS dropped and counted, never repaired by name.
- [Threshold drift hides weak matches] -> recalibration task plus caffeine negative test.
- [Added candidates change existing surrogate answers] -> eval cassettes re-run 3x
  (per past eval findings); isohexane to n-hexane scenario must still pass.
- [Compound classes are broad (e.g. glycol ethers, 97 rows)] -> membership is binary and
  disclosed; no similarity is claimed.

## Migration Plan

1. Land loader, config and tests (no behaviour change until wired).
2. Wire the tool step and schema; update emissions identifier handling.
3. Rebuild the catalog (`uv run python -m scripts.build_tri_embeddings`), recalibrate, commit shards.
4. Prompt, descriptions, evals. Rollback: revert the commit; shards and CSV are data only.

## Open Questions

- Should inorganic members ever be read-across candidates (e.g. a different fingerprint)?
  Deferred; not needed for this change.
