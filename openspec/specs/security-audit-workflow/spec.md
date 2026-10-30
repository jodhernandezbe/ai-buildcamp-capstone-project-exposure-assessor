# security-audit-workflow Specification

## Purpose
An independent security audit of every change, layered over the project's deterministic
scanners, so that no change is judged only by the agent that wrote it and no audit is skipped by
forgetting.

## Requirements

### Requirement: Independent auditor
The audit of a change SHALL be performed by a subagent with its own context, dispatched with the
repository root, the diff range, the changed files and the project's exclusions, and with no
conclusion, hypothesis or reassurance from the session that produced the change. The dispatching
session SHALL NOT audit the same diff in parallel. The auditor SHALL have no write, execution or
network capability.

#### Scenario: Dispatch carries no hypothesis
- **WHEN** a change is audited
- **THEN** the auditor receives the diff, the files and the exclusions, and nothing stating what the change is believed to do safely

#### Scenario: Auditor cannot act
- **WHEN** the auditor runs
- **THEN** it only reads, searches and runs read-only git, and it reports what it could not settle rather than running the code

### Requirement: Findings are traced and cited
A reported finding SHALL name an attacker-controlled input, a dangerous operation it reaches and
the absence of an effective check, each with a `file:line`, plus who supplies the input and what
they gain. A candidate that cannot be traced end to end SHALL NOT be reported as a finding.
Tests, fixtures, mocks and cassettes SHALL be excluded from the audited scope, and a defect that
exists only in them SHALL NOT be reported. The auditor SHALL report the absence of findings
plainly rather than filling the report.

#### Scenario: Untraceable candidate
- **WHEN** the auditor suspects a defect but cannot trace a path to it
- **THEN** it appears as a note or as "not audited", never as a finding

#### Scenario: Clean change
- **WHEN** a change introduces no exploitable defect the auditor can confirm
- **THEN** the report says so in one sentence

### Requirement: Deterministic scanners run first and are reported honestly
Before the auditor is dispatched, the project's configured scanners for secrets, security lint
and dependency advisories SHALL run over the change, each reported as pass, fail or not
configured, with the command used. A scanner that is absent SHALL be reported as not configured,
never as a pass. Output stating that nothing was checked SHALL be treated as a failure to
investigate, not as a pass. Dependency advisories SHALL be owned by this layer and SHALL NOT be
reported by the auditor.

#### Scenario: Scanner skipped its input
- **WHEN** a scanner reports that it had no files to check
- **THEN** the audit reports that layer as failed and investigates, rather than recording a pass

#### Scenario: Layer absent
- **WHEN** the project has no semantic static analysis configured
- **THEN** the report names it as not configured

### Requirement: Unaudited source changes are caught before a turn ends
When a turn ends with changes to source files that have not been audited, the project SHALL ask
for the audit before the work is called done. Changes to documentation, planning artifacts, lock
files and images SHALL NOT trigger it. It SHALL stay silent once the current diff has been
recorded as audited, SHALL NOT trigger again while the session is already continuing because of
it, and SHALL NOT itself run a scan.

#### Scenario: Source changed and unaudited
- **WHEN** a turn ends after editing a source file that has not been audited
- **THEN** the audit is requested before the turn finishes

#### Scenario: Brand-new source file
- **WHEN** a turn ends having added a source file that git does not yet track and does not ignore
- **THEN** the audit is requested, because a new module is the commonest way new code arrives

#### Scenario: Documentation only
- **WHEN** a turn ends having changed only Markdown files
- **THEN** nothing is requested

#### Scenario: Tests only
- **WHEN** a turn ends having changed only tests, fixtures, mocks or cassettes
- **THEN** nothing is requested, because a defect in code that is not shipped is not exploitable

#### Scenario: Already audited
- **WHEN** the audit has run and recorded the current diff
- **THEN** the turn ends without a further request

#### Scenario: No repeated request
- **WHEN** the session is already continuing because of this request
- **THEN** it is not made again

### Requirement: Exclusions are narrow and reasoned
A finding class the project decides is not a defect here SHALL be recorded as one line naming
what is excluded and why, and SHALL be read by the auditor on every run. An exclusion SHALL be
specific enough that it could not hide an unrelated defect.

#### Scenario: Recording an exclusion
- **WHEN** the team judges a reported finding to be noise in this project
- **THEN** a one-line rule with its reason is added and later audits apply it
