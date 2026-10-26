# assessment-report Specification

## Purpose

Turns a thread's screening assessment into a Word document laid out like an EPA screening-level
assessment, so the findings can be reviewed, shared and filed outside the app.

## Requirements

### Requirement: Report endpoint
`GET /api/v1/chat/threads/{thread_id}/report` SHALL return, for a thread the program holds whose
workspace has a chemical result or at least one facility, a Word document
(`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) as an attachment
whose file name is built from the configured pattern, the chemical's CAS number (or "chemical"
when none) and the generation date. A thread the program does not hold SHALL be answered 404, a
thread with nothing to report 409, a thread running a turn 409, and a malformed id 422, each
with the generic error body. The endpoint SHALL NOT run the agent, call any tool or external
service, or change the thread, apart from marking it as recently used.

#### Scenario: Report for an assessed thread
- **WHEN** the report of a thread holding one assessed facility is requested
- **THEN** the response is 200 with the Word media type and an attachment file name ending in `.docx`

#### Scenario: Unknown thread
- **WHEN** the report of a thread the program does not hold is requested
- **THEN** the response is 404 with a generic message and a correlation id

#### Scenario: Empty thread
- **WHEN** the report of a held thread with no chemical result and no facility is requested
- **THEN** the response is 409 with a generic message

#### Scenario: Thread running a turn
- **WHEN** the report is requested while the thread's turn is running
- **THEN** the response is 409 and the running turn is unaffected

### Requirement: Report sections
The document SHALL open with a title page block (configured title, chemical name and CAS
number, generation date and time, and the configured screening-level disclaimer) followed by
these numbered sections in order: 1 Summary of findings, 2 Chemical identity and properties,
3 Data sources, 4 Releases, 5 Exposure assessment, 6 Risk characterization, 7 Uncertainties and
limitations, 8 Assessor summary. Section headings SHALL come from configuration. A section with
no data SHALL still appear, with a sentence saying no result was reported for it. Every page
SHALL carry a header with the app logo (a configured PNG copy of the app's logo) beside the
configured app name, and a footer with the configured page label giving the page number and the
page count as Word fields, so Word keeps them current.

#### Scenario: Header and page numbers
- **WHEN** a report is generated
- **THEN** its page header holds the logo image and the app name, and its page footer holds a `PAGE` field followed by a `NUMPAGES` field

#### Scenario: Missing logo is a setup error
- **WHEN** the configured logo file does not exist or is not a PNG
- **THEN** loading the settings fails and names `ui.report.logo`

#### Scenario: Section order
- **WHEN** a report is generated for an assessed thread
- **THEN** its headings read, in order, the eight configured section headings after the title block

#### Scenario: Empty section kept
- **WHEN** the thread has a chemical result but no facility
- **THEN** sections 4, 5 and 6 are present and each says no result was reported

### Requirement: Report content comes only from the workspace
Every value in sections 1 to 7 SHALL come from the thread's latest workspace state (chemical
properties and read-across provenance, facilities with releases, operating hours, industry,
conditions of use, stacks, receptors, meteorology, exposure ranges, screening outcome, risk
summary, warnings). The report SHALL NOT compute, estimate or convert any scientific value; it
SHALL print each value with its unit as given in the workspace contract and with the configured
number of significant digits. An absent value SHALL print as "not reported", followed by its
reason when the workspace gives one, never as 0 or a dash.

- Section 1 SHALL state the highest worst-case and representative hazard quotient and cancer
  risk with the facility and stack they occur at and their status against the thresholds, and
  the number of facilities assessed, and name the distinct TSCA life cycle stages and conditions
  of use the facilities reported (or "not reported" when there are none).
- Section 2 SHALL tabulate CAS number, name, molecular weight, RfC and IUR, each with its
  source, and the read-across outcome (kind, surrogate, similarity scores, applicability
  domain).
- Section 3 SHALL list each distinct source named anywhere in the workspace (chemical property
  sources, stack parameter source and tier, industry, operating hours, receptors, meteorology),
  with what it supplied.
- Section 4 SHALL tabulate per facility: FRS ID, name, location, NAICS, reporting year, medium,
  total release with unit, emission rate (g/s), operating hours and their source, and conditions
  of use and life cycle stages.
- Section 5 SHALL give per facility the stacks evaluated, the stack parameters with their tier,
  meteorology, receptor population and radius, and the worst-case and representative
  concentration ranges.
- Section 6 SHALL first tabulate risk by TSCA life cycle stage and condition of use: one row per
  condition of use of each facility (life cycle stage, condition of use category, TRI activity,
  facility, worst-case hazard quotient and cancer risk, status), ordered by life cycle stage then
  condition of use, with facilities that report none last showing why. It SHALL state that risk
  is estimated per facility and repeated under each of its conditions of use, never apportioned.
  It SHALL then tabulate per facility the hazard quotient and cancer risk ranges, the screening
  outcome and its reason, and state the thresholds the statuses were judged against.
- Section 7 SHALL list every warning in the workspace, grouped by where it arose, and every
  screening default used (receptors or meteorology), and every unattributed result with its
  reason.

#### Scenario: Absent value
- **WHEN** the chemical's IUR is absent from the workspace
- **THEN** section 2 prints "not reported" for IUR and does not print 0

#### Scenario: No computed values
- **WHEN** a report is generated from a workspace fixture
- **THEN** every number in sections 1 to 7 equals a number in that workspace, rounded only to the configured significant digits

#### Scenario: Risk by condition of use
- **WHEN** a facility reports two conditions of use in different life cycle stages
- **THEN** section 6 lists it once under each, with the same worst-case values, before the per facility table

#### Scenario: Screening defaults disclosed
- **WHEN** a facility's meteorology is a screening default
- **THEN** section 7 lists that facility's meteorology as a screening default

### Requirement: Model-generated summary is labelled
Section 8 SHALL contain the text of the thread's last assistant message, rendered from Markdown
to document paragraphs, lists and tables without raw HTML, under a note stating it was written
by the AI assistant, may contain errors, and is not a source of the values in sections 1 to 7.
When the thread has no assistant message, section 8 SHALL say no assistant summary is
available. The report SHALL NOT include tool calls, tool results, user messages, keys,
exception text or request headers.

#### Scenario: Assistant answer included
- **WHEN** the thread's last assistant message contains a Markdown table
- **THEN** section 8 shows the label note followed by that table as a document table

#### Scenario: No secrets
- **WHEN** a report is generated for a thread whose turns used stored API keys
- **THEN** the document contains no key material and no request headers
