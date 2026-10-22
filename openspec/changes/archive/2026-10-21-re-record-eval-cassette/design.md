## Context

Replay fails closed on an unrecorded call. The agent takes either route for a 2-facility
chemical (9 of 13 runs by hand, 4 by the batch tool), so one recording does not cover both.

## Decisions

- Record both routes: run `uv run python -m evals record full-assessment-with-nei-stacks`
  until each route has been recorded once, merging nothing by hand; if the recorder keeps only
  the last run, record the by-hand route (the longer one) and accept that a batch-route replay
  reports its call unrecorded until the recorder keeps several runs. Decide when recording.
- Verify CompTox first: `curl https://comptox.epa.gov/ctx-api/chemical/search/equal/110-54-3`
  must return 200 (the certificate expired 2026-10-21 23:59 GMT).

## Risks

- The report judge varies run to run (weather source not named in 3 of 13 runs); that is
  report wording, out of scope here.
