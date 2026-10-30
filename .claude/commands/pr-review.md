---
description: Review a pull request with an independent reviewer, ask the user about anything suspicious, then post inline comments and optionally approve, all through the GitHub CLI
argument-hint: [PR number or branch, default the current branch's PR]
---

Review the pull request named by `$ARGUMENTS` (default: the pull request for the current
branch). Everything runs through `gh`. Nothing is posted to GitHub until the user says so in
this turn.

## 1. Check the tooling

Run `gh auth status`. If `gh` is missing or not authenticated, stop and tell the user to run
`! gh auth login` themselves (the `!` prefix runs it in this session so the browser prompts
reach them), pointing at `.claude/pr-review-gh-setup.md`. Never try to authenticate for them.

## 2. Read the pull request

- `gh pr view <pr> --json number,title,body,author,baseRefName,headRefName,isDraft,files,url`
- `gh pr diff <pr>`
- Existing conversation: `gh pr view <pr> --comments`, so you never repeat a comment someone has
  already made, and you can see what the author already explained.
- Check for review history: a second review of the same PR comments only on what changed since.

If the pull request is a draft, say so and ask whether to continue.

## 3. Dispatch the reviewer

Dispatch the `pr-reviewer` subagent with the Agent tool. Give it the repository root, the base
and head refs, the changed files, the pull request title and body, and the path of
`.claude/pr-review-rules.md` if it exists. Do not give it your own reading of the change or any
conclusion: a reviewer handed a hypothesis returns it confirmed. Do not review the diff yourself
in parallel.

For a large pull request (more than roughly 40 files or several unrelated areas), dispatch one
reviewer per area and merge the reports.

Security is out of scope here; `/security-audit` owns it. If the reviewer raises something that
looks dangerous, carry it as a question and say the audit should settle it.

## 4. Ask the user about the suspicious things

Take the reviewer's questions, plus any finding whose severity you are unsure of. Put them to
the user with AskUserQuestion, at most four at a time, each naming the file and line and what
caught the reviewer's eye. Give concrete options where they exist (for example: "intentional,
leave it", "worth a comment", "blocking"). Never post a comment about something the user has
just explained.

If the reviewer raised nothing and found nothing blocking, skip this step and say so.

## 5. Agree what gets posted

Show the user a numbered list of what you propose to post: each inline comment with its
`file:line` and exact text, plus the review body. Keep comment text short, specific and free of
praise; a comment should say what is wrong and what would fix it.

Then ask for the verdict with AskUserQuestion:

- **Comment** posts the comments without a verdict;
- **Approve** posts them and approves;
- **Request changes** posts them and requests changes;
- **Post nothing** ends the review here.

Respect what `.claude/pr-review-rules.md` says about approval. Never choose approval yourself:
an approval is the user's signature, and the user must pick it in this turn. Do not approve a
pull request authored by the account that is posting, and say so if that is the case.

## 6. Post

Write the payload to a temporary file in the scratch directory:

```json
{"body": "...", "event": "COMMENT",
 "comments": [{"path": "src/x.ts", "line": 42, "side": "RIGHT", "body": "..."}]}
```

Run `bash .claude/scripts/pr-review-post.sh <pr> <payload.json> --dry-run` first and show the
result. The script checks that every comment anchors to a line this diff touches and moves any
that do not into the review body, so nothing is dropped silently. Then run it without
`--dry-run` and report the review URL it prints.

`line` is the line number in the head revision for `side: "RIGHT"`, and in the base for
`"LEFT"`. Use `RIGHT` for added or changed lines, `LEFT` only when commenting on a deleted line.

## 7. Close

Report what was posted and the URL. If findings were left unposted at the user's request, say
which. Do not merge, and do not offer to.
