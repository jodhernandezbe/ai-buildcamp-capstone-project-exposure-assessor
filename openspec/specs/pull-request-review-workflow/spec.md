# pull-request-review-workflow Specification

## Purpose
An independent review of a pull request, run from the command line, that puts the reviewer's
questions to a human before anything becomes public and posts only what that human approved.

## Requirements

### Requirement: Independent reviewer
The review of a pull request SHALL be performed by a subagent with its own context, dispatched
with the repository root, the base and head refs, the changed files, the pull request title and
body, and the project's review rules, and with no conclusion from the session dispatching it.
The dispatching session SHALL NOT review the same diff in parallel. The reviewer SHALL have no
capability to post, comment, approve, merge or write.

#### Scenario: Reviewer cannot post
- **WHEN** the reviewer finishes
- **THEN** it has returned a report and has published nothing

#### Scenario: Large pull request
- **WHEN** a pull request spans many files or several unrelated areas
- **THEN** reviewers are dispatched per area and the reports are merged, with anything unreviewed named

### Requirement: Findings are anchored, concrete and justified by a project rule
A reported finding SHALL carry a `file:line` in the diff, one sentence naming the defect, a
concrete failure (the input or state and the wrong result), a severity of blocking, consider or
nit, and the smallest fix in words. A judgement that cannot cite a project rule or a neighbouring
pattern SHALL be raised as a question rather than a finding. The review SHALL cover correctness,
contracts, project conventions, tests, data modelling and efficiency at a named scale, and SHALL
NOT report what a formatter, linter or type checker already enforces, nor security defects.

#### Scenario: Taste without a rule
- **WHEN** the reviewer prefers a different approach but no project rule or neighbouring pattern supports it
- **THEN** it appears as a question, not as a finding

#### Scenario: Security defect noticed
- **WHEN** the reviewer sees something that looks exploitable
- **THEN** it is raised as a question naming the security audit as the place to settle it

#### Scenario: Speculative performance
- **WHEN** a performance concern has no concrete scale behind it
- **THEN** it is not reported as a finding

### Requirement: The author answers before anything is posted
The reviewer's questions SHALL be put to the user before any comment text is finalised, each
naming the file, the line and what prompted it. A matter the user explains in that exchange
SHALL NOT then be posted as a comment.

#### Scenario: Question answered
- **WHEN** the user explains that a flagged choice is intentional
- **THEN** no comment about it is posted

#### Scenario: Nothing suspicious
- **WHEN** the reviewer raises no question and finds nothing blocking
- **THEN** the user is told so and is not asked anything

### Requirement: The human chooses the verdict
Before anything is sent, the user SHALL see every comment with its `file:line` and exact text,
and SHALL choose between commenting, approving, requesting changes and posting nothing. The
verdict SHALL NOT be chosen by the agent, and approval SHALL NOT be posted without the user
selecting it in that turn. The project's own approval rules SHALL be respected.

#### Scenario: Approval requires the user
- **WHEN** a review is ready and nothing is blocking
- **THEN** it is still the user who selects approval, and the agent never selects it

#### Scenario: Post nothing
- **WHEN** the user chooses to post nothing
- **THEN** the review ends with nothing sent and the findings reported in the session only

### Requirement: Posting is validated before it is sent
A review SHALL be posted through the GitHub CLI with an event of comment, approval or a request
for changes, rejecting any other value. Every inline comment SHALL anchor to a line the pull
request's diff touches on the stated side; a comment that does not SHALL be moved into the
review body and reported, never silently dropped. The payload SHALL be previewable without
sending. Missing or unauthenticated tooling SHALL stop the posting with the setup instructions,
and SHALL NOT be worked around.

#### Scenario: Comment outside the diff
- **WHEN** a comment names a line the diff does not touch
- **THEN** it is moved into the review body, the move is reported, and the rest post normally

#### Scenario: Invalid event
- **WHEN** a review event other than the three allowed values is given
- **THEN** nothing is posted and the error names the allowed values

#### Scenario: CLI not authenticated
- **WHEN** the GitHub CLI is missing or not logged in
- **THEN** posting stops with the setup instructions and the user performs the login themselves
