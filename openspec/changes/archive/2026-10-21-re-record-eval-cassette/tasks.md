## 1. Certificate waiver

- [x] 1.1 `[comptox].accept_expired_certificate` (default false) and the client's TLS context that skips the dates only; loader and client tests

## 2. Recording

- [x] 2.1 CompTox reached through the waiver on 2026-10-21 (probe: name, RfC and IUR returned); `uv run python -m evals record full-assessment-with-nei-stacks`
- [x] 2.2 The cassette holds `fetch_chemical_properties` with the name and benchmarks and the by-hand route's calls (NEI with `eis_ids`, weather, residents); a batch-route replay reports its call unrecorded (the recorder keeps one run)

## 3. Verification

- [x] 3.1 `uv run pytest -m eval` six times on 2026-10-21: 14/14 in three runs; the report judge failed in at least one (its known run-to-run variance), every deterministic check passed in every run whose details were kept, the source check included. The waiver was set back to false before the commit
