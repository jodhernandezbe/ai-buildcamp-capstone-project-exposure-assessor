## ADDED Requirements

### Requirement: Cassette current with the tools
A scenario's cassette SHALL be recorded while every service it needs answers (a recording made during an outage carries the outage, not the data), and SHALL hold a recording for every call the agent can make on either route it may take (the batch assessment, or the chain by hand with the current tool signatures). A replay that hits an unrecorded call SHALL fail the scenario and be answered by re-recording it, never by editing the cassette.

#### Scenario: Tool signature changed
- **WHEN** a tool the agent calls gains an argument and the agent now passes it
- **THEN** the replay reports the call as unrecorded and the scenario is re-recorded

#### Scenario: Service outage during recording
- **WHEN** a service fails while a scenario is being recorded
- **THEN** the recording is not kept as the cassette
