## MODIFIED Requirements

### Requirement: Conversation threads
The program SHALL keep each thread's message history, dashboard state and session usage in
process memory, so follow-up turns see earlier turns, and SHALL NOT persist threads to disk.
Clearing the workspace in the UI SHALL reset the thread it shows. The program SHALL keep at
most a configured number of threads: when a new thread would exceed it, the thread used least
recently that is not running a turn SHALL be forgotten first. A running thread SHALL NOT be
evicted. A thread SHALL be resettable, and only one turn per thread SHALL run at a time.

#### Scenario: Follow-up turn
- **WHEN** a second turn is sent on the same thread
- **THEN** the agent receives the first turn's messages and the dashboard keeps the earlier facilities

#### Scenario: Reset
- **WHEN** the thread is reset
- **THEN** its history, dashboard and session usage are cleared

#### Scenario: Reset during a turn
- **WHEN** a reset is requested while the thread is running a turn
- **THEN** the request is answered 409 and the running turn is unaffected

#### Scenario: Concurrent turn on one thread
- **WHEN** a turn is submitted while another turn of the same thread is still running
- **THEN** the second request is answered 409 and the running turn is unaffected

#### Scenario: Retention limit
- **WHEN** the configured maximum of threads is held and a turn starts on a new thread
- **THEN** the least recently used idle thread is forgotten and the new thread runs

#### Scenario: Running thread not evicted
- **WHEN** the limit is reached and every held thread is running a turn
- **THEN** no running thread is forgotten
