## ADDED Requirements

### Requirement: Recordings cover every route to the same outcome
A scenario SHALL be able to list extra tool calls (a tool and its arguments). Recording mode
SHALL make them after the agent run, through the same recording wrapper, so the cassette holds
the outputs of routes the agent did not take in that run. A separate recording command SHALL
make only a scenario's extra calls, without running the agent, and SHALL add their outputs to
the existing cassette, keeping every recording already there; a recording for the same tool and
arguments is replaced by the new one. Extra calls SHALL be made with the tool's full argument
schema so their key equals the key of an agent call that omits the optional arguments.

#### Scenario: Batch route recorded beside the by-hand route
- **WHEN** a scenario lists the batch assessment as an extra call and its cassette is recorded
- **THEN** the cassette holds the batch output as well as the per-facility outputs, and a replayed agent that takes either route finds its recordings

#### Scenario: Extending a cassette
- **WHEN** only the extra calls are recorded for a scenario that already has a cassette
- **THEN** the earlier recordings stay and the extra outputs are added

#### Scenario: Call omitting optional arguments
- **WHEN** the agent calls a recorded tool with only its required arguments
- **THEN** the call finds the recording made from an extra call that gave the same required arguments
