## MODIFIED Requirements

### Requirement: Conversation threads
The program SHALL keep each thread's message history, dashboard state and session usage in
process memory, so follow-up turns see earlier turns, and SHALL NOT persist threads to disk.
Starting a new analysis in the UI SHALL leave earlier threads in place. The program SHALL keep at
most a configured number of threads: when a new thread would exceed it, the thread used least
recently that is not running a turn SHALL be forgotten first. A running thread SHALL NOT be
evicted. A thread SHALL still be resettable, and only one turn per thread SHALL run at a time.

#### Scenario: Follow-up turn
- **WHEN** a second turn is sent on the same thread
- **THEN** the agent receives the first turn's messages and the dashboard keeps the earlier facilities

#### Scenario: Reset
- **WHEN** the thread is reset
- **THEN** its history, dashboard and session usage are cleared

#### Scenario: Concurrent turn on one thread
- **WHEN** a turn is submitted while another turn of the same thread is still running
- **THEN** the second request is answered 409 and the running turn is unaffected

#### Scenario: Retention limit
- **WHEN** the configured maximum of threads is held and a turn starts on a new thread
- **THEN** the least recently used idle thread is forgotten and the new thread runs

#### Scenario: Running thread not evicted
- **WHEN** the limit is reached and every held thread is running a turn
- **THEN** no running thread is forgotten

## ADDED Requirements

### Requirement: Thread snapshot
`GET /api/v1/chat/threads/{thread_id}` SHALL return, for a thread the program holds, the
thread's user and assistant messages in order (text only, without tool calls or tool
results), its latest workspace state (or the empty state before any tool result) and its session
usage, all in the shapes of the shared wire contract. A thread the program does not hold SHALL
be answered 404 with the generic error body. The endpoint SHALL NOT run the agent or change the
thread, apart from marking it as recently used. Its responses SHALL NOT contain keys,
exception text or request headers. A malformed thread id SHALL be answered 422.

#### Scenario: Snapshot of a held thread
- **WHEN** a thread with two finished turns is requested
- **THEN** the response lists its four user and assistant messages in order, the workspace last sent for it, and its session usage

#### Scenario: Unknown thread
- **WHEN** a thread id the program does not hold is requested
- **THEN** the response is 404 with a generic message and a correlation id

#### Scenario: Snapshot during a turn
- **WHEN** a thread is requested while its turn is running
- **THEN** the response holds what has been recorded so far and the running turn is unaffected
