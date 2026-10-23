## Context

`Recorder` wraps each network tool so a live call is saved by tool name and canonical arguments,
and `save` replaces the file. `replay_tools` clones every non-live tool, including
`assess_facilities`, which has no recording in the by-hand cassette. The checks read only the
model-facing output (`call.output`), which for the batch tool is its content, and already
handle either route.

## Decisions

- **Extra calls, not a forced route.** The agent cannot be made to take a route, and a check
  that ignores unrecorded calls would hide real gaps. Recording the batch call directly makes
  both routes replayable; an unrelated call still fails closed.
- **Same wrapper, full schema.** The extra call goes through the recorder's clone with
  `invoke({"cas_number": ...})`; the clone's function receives every schema field with its
  default, which is also what a replayed agent call produces, so the keys match.
- **Merge by seeding.** `Recorder.seed(path)` loads the rows of an existing cassette; saving
  writes seeded and new rows, new winning per key. `record` starts empty (a fresh agent run
  replaces the cassette, then adds extras); `record-extra` starts seeded.
- **Extras are data on the scenario** (`ExtraCall(tool, args)`), not code in the suite.
- The batch output is recorded as the live tool returns it, never edited.

## Risks / Trade-offs

- [The batch recording can go stale when its tools change] -> same as every recording;
  re-record with `record-extra`.
- [Seeded rows keep outputs of calls no longer made] -> harmless: unused rows are never replayed.
- [A live recording run is needed] -> one run of two facilities.
