## 1. Harness

- [x] 1.1 `Recorder.seed(path)`; `save` keeps seeded rows; tests (kept, replaced per key, missing file)
- [x] 1.2 `ExtraCall` and `Scenario.extra_calls`; the full-assessment scenario lists `assess_facilities`
- [x] 1.3 `suite.record_extras` (shared by `record` and the new `record-extra`); CLI command; tests with fake tools
- [x] 1.4 Test that an extra call's key equals the key of a replayed agent call omitting optional arguments

## 2. Recording and verification

- [x] 2.1 Run `record-extra` for the full-assessment scenario (live) and check the cassette keeps its by-hand rows
- [x] 2.2 Replay both routes offline: a call to `assess_facilities` with only `cas_number` finds the recording
- [x] 2.3 Update `evals/CLAUDE.md`; ruff, pyright, bandit, function length, pytest, pre-commit
- [x] 2.4 Run the evaluations three times and count unrecorded-call failures
