## 1. Hook configuration

- [x] 1.1 Add the `asottile/add-trailing-comma` repo block to `.pre-commit-config.yaml` before the ruff block
- [x] 1.2 Run `uv run pre-commit autoupdate --repo https://github.com/asottile/add-trailing-comma` to pin the latest `rev`

## 2. Verification

- [x] 2.1 Add `tests/test_pre_commit_config.py` asserting the hook is present and listed before `ruff-format` (include a negative case: ordering helper rejects the reverse)
- [x] 2.2 Check on a scratch Python file with a multi-line call missing the comma that the hook adds it, and that a single-line call is untouched
- [x] 2.3 Run `uv run pre-commit run --all-files` twice on a scratch copy; confirm the second pass changes nothing (formatter-stable) and that unstaged files are not rewritten

## 3. Docs and gates

- [x] 3.1 Add a trailing-comma line to the Code style section of `CLAUDE.md` (keep under 80 lines; `tests/test_claude_md.py`)
- [x] 3.2 Run pytest, ruff format/check, pyright, bandit and the function-length check
