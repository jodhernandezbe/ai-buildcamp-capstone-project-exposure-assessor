## ADDED Requirements

### Requirement: Multi-line constructs end with a trailing comma
The pre-commit pipeline SHALL add a trailing comma to every Python call, definition,
list, tuple, set, dict, subscript and import group whose closing bracket is on its own line
and whose last element lacks one.

#### Scenario: Missing comma is added
- **WHEN** a staged Python file has a multi-line call whose last argument has no trailing comma
- **THEN** the hook rewrites the file with the comma added and the commit is stopped for re-staging

#### Scenario: Already terminated construct is untouched
- **WHEN** every multi-line construct in a staged file already ends with a trailing comma
- **THEN** the hook makes no change and passes

#### Scenario: Single-line construct is untouched
- **WHEN** a call or literal fits on one line
- **THEN** no trailing comma is added

### Requirement: Only edited Python files are processed
The hook SHALL run only on Python files included in the commit and SHALL NOT rewrite files
that are not staged.

#### Scenario: Unstaged file is not rewritten
- **WHEN** a Python file with missing trailing commas is not part of the commit
- **THEN** the hook does not modify it

### Requirement: Compatible with the formatter
The hook SHALL run before `ruff-format`, and its output SHALL be stable under
`ruff format` so the two hooks do not alternate rewrites.

#### Scenario: Hook output is formatter-stable
- **WHEN** the hook has added commas and `ruff format` then runs
- **THEN** a second run of both hooks changes nothing
