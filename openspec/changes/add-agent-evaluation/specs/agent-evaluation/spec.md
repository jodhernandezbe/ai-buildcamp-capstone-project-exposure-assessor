## Purpose

Behavioral evaluation of the exposure-assessor agent: runs the real agent with an OpenAI chat
model on scripted scenarios and checks which tools it calls, with what arguments, and what its
final report says, so regressions in prompts or tool descriptions are caught.

## ADDED Requirements

### Requirement: Scenario runs are captured as records
The evaluation SHALL run the production agent graph (the registered tools with their real
names, descriptions and argument schemas, and the production system prompt) once per scenario
and SHALL capture each run as one record holding: the scenario id, the user query, every tool
call in order with its name and arguments, every tool output, the final report text, and
whether the run completed or the error that ended it. A run that ends in an error SHALL still
produce a record.

#### Scenario: Completed run
- **WHEN** a scenario is run and the agent finishes with a final answer
- **THEN** its record lists the tool calls in the order made, their outputs and the final report, and is marked completed

#### Scenario: Run ends in an error
- **WHEN** the agent run raises (for example it exceeds the step limit)
- **THEN** the record is marked not completed with the error message and the scenario fails

### Requirement: The agent under test uses the program's chat model
The agent under test SHALL be driven by the same chat model the program runs: the one
configured in the agent settings (provider, model, API-key variable, timeout and step limit),
built by the program's own chat model factory. The evaluation SHALL NOT name or construct an
agent model of its own. The judge model SHALL come from the evaluation settings. When an API key
is not set, evaluation runs SHALL be skipped with a message naming the variable, not fail.

#### Scenario: Model swapped in settings
- **WHEN** the agent model name is edited in the settings
- **THEN** the program and the next evaluation run both use that model

#### Scenario: Missing key
- **WHEN** the OpenAI key variable is unset or empty
- **THEN** the evaluation tests are skipped and say which variable is missing

### Requirement: Tool outputs are recorded from live services and replayed
Tools that call network services SHALL be replayed from recordings made by running those tools
against the live services; recordings SHALL NOT be written by hand. Tools that need no network
(the exposure calculation) SHALL run for real during replay. A replayed tool SHALL return the
recorded output for a call whose arguments match a recording. A call with no matching recording
SHALL fail closed: the tool returns an error result to the agent saying no recording exists, and
the record marks the call as unrecorded so the scenario fails with a message to re-record. A
recording mode SHALL run the scenario with the live tools and save every network tool output.

#### Scenario: Recorded call
- **WHEN** the agent calls a network tool with arguments that match a recording
- **THEN** it receives the recorded output and no network request is made

#### Scenario: Unrecorded call
- **WHEN** the agent calls a network tool with arguments that have no recording
- **THEN** the tool returns an error result, the call is marked unrecorded and the scenario fails naming the call

#### Scenario: Offline tool
- **WHEN** the agent calls the exposure calculation during replay
- **THEN** the real calculation runs on the arguments the agent passed

#### Scenario: Recording
- **WHEN** a scenario is run in recording mode
- **THEN** each network tool output is saved so a later replay reproduces it

### Requirement: Deterministic checks score tool use and completion
Each scenario SHALL declare deterministic checks evaluated on its record by the evaluation
framework, each yielding pass or fail with a reason: which tools must, must not, or may be
called; how many times a tool is called relative to the tool outputs (for example once per stack
candidate); which arguments a call must carry (for example the CAS number asked for); call order
where it matters; that no call was unrecorded; and that the run completed. Checks SHALL compare
against values found in the record's tool outputs, never against numbers written into the check.

#### Scenario: Forbidden tool called
- **WHEN** a scenario forbids a tool and the record contains a call to it
- **THEN** that check fails and names the call

#### Scenario: Count tied to tool output
- **WHEN** a check requires one exposure calculation per stack candidate
- **THEN** the expected count is taken from the stack candidates in the record, and a different count fails

### Requirement: LLM judges score report qualities
Report qualities that code cannot verify SHALL be scored by an OpenAI judge model named in the
evaluation settings. Each judge SHALL answer one narrow pass/fail criterion about the final
report, given the report and, where needed, the tool outputs, and SHALL record its reasoning.
A judge that cannot be reached SHALL make its check fail, not pass.

#### Scenario: Criterion met
- **WHEN** the final report satisfies a judge criterion
- **THEN** the judge check passes and its reasoning is kept in the results

#### Scenario: Judge unavailable
- **WHEN** the judge call fails
- **THEN** the check fails with the error as its reason

### Requirement: Each evaluation run writes a report
Each evaluation run SHALL write a human-readable report showing, per scenario, every check with
its result and reason, and an overall pass/fail per scenario. Reports SHALL be written to a
configured directory that is not committed.

#### Scenario: Report written
- **WHEN** an evaluation run finishes
- **THEN** a report file exists in the configured directory with one entry per scenario and check

### Requirement: Evaluations are opt-in
Evaluation tests SHALL be marked so they are excluded from the default test run and from the
pre-commit hooks, and SHALL run when the marker is selected explicitly.

#### Scenario: Default test run
- **WHEN** the default test command runs
- **THEN** no evaluation test runs and no model is called

#### Scenario: Explicit selection
- **WHEN** the evaluation marker is selected
- **THEN** the evaluation tests run

### Requirement: Scenario catalogue
The evaluation SHALL keep a catalogue of scenarios, each with an id, the user query, its
recordings and its checks. A scenario that depends on behavior not yet implemented SHALL be
listed as blocked with the reason and SHALL NOT be run. The catalogue SHALL cover: happy paths,
tool use and fallback order, edge cases, and failure modes.

#### Scenario: Blocked scenario
- **WHEN** the catalogue lists a scenario as blocked
- **THEN** it is reported as skipped with its reason

### Requirement: Chemical given by name only
The catalogue SHALL include a scenario in which the user names a chemical by its common name
(formaldehyde) and gives no CAS number. It SHALL pass only when: the run completed; no tool was
called; the final report states no CAS number; and an LLM judge confirms the reply asks the user
for the CAS registry number and presents no facility, concentration or risk result.

#### Scenario: CAS filled in from memory
- **WHEN** the agent calls a tool with a CAS number it supplied itself
- **THEN** the no-tool-call check fails and names the call

#### Scenario: Reply does not ask for the CAS number
- **WHEN** the final reply does not ask for the CAS number
- **THEN** the LLM judge check fails with the judge's reasoning

### Requirement: Full assessment of a facility with its own stacks
The catalogue SHALL include a scenario asking for an assessment of a chemical given by CAS number
whose recorded inventory returns facilities that have NEI stack candidates. It SHALL pass only
when: the run completed with no unrecorded call; the chemical's properties and the emissions
inventory were requested with the CAS number asked for; every facility the agent assessed had
its NEI stacks requested with its `frs_id`, its weather and its population requested with that
facility's coordinates; the exposure calculation ran once per NEI stack candidate of each
assessed facility; the industry, SCC process and SCC stack tools were not called for a facility
that had NEI candidates; and a judge confirms the report gives a summary, a per-facility table
with units showing the range over stacks and both the worst and the representative case, the
source of each input, and a limitations section.

#### Scenario: One stack evaluated out of several
- **WHEN** a facility has several NEI candidates and the agent runs the exposure calculation for only one
- **THEN** the call-count check fails

#### Scenario: Unneeded fallback
- **WHEN** a facility has NEI candidates and the agent also calls the SCC stack tool for it
- **THEN** the forbidden-tool check fails

#### Scenario: Complete assessment
- **WHEN** the agent follows the chain for every facility it assesses and writes the full report
- **THEN** every check passes
