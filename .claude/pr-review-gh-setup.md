# GitHub CLI setup for `/pr-review`

The review is posted from your own GitHub account, so the CLI has to be installed and
authenticated once per machine. A reviewer who has never posted from the command line does this
once; after that `/pr-review` works without any further setup.

## 1. Install

```sh
brew install gh          # macOS
# or: https://github.com/cli/cli#installation
```

## 2. Authenticate

```sh
gh auth login
```

Choose GitHub.com, HTTPS, and authenticate in the browser. In Claude Code, run it yourself with
a leading `!` so the prompts reach you: `! gh auth login`. Claude cannot answer an interactive
login on your behalf.

Check it:

```sh
gh auth status
gh repo view --json nameWithOwner
```

## 3. Scopes

The browser flow grants what reviewing needs: reading the repository and writing pull request
reviews. If your token came from somewhere else and the post fails with a permissions error:

```sh
gh auth refresh -s repo
```

## 4. What posting does

Everything `/pr-review` posts is attributed to your account, not to an app or a bot. You see the
exact payload before anything is sent, and nothing is posted or approved without you saying so
in that turn.

## Reviewing your own pull request

GitHub allows a comment on your own pull request but refuses a verdict: both approval and a
request for changes come back as a 422. The posting script detects this before sending and
tells you, and the findings can still go up as a comment with the intended verdict written into
the body. A real verdict needs a second account.

## Organisations

If the repository belongs to an organisation with SAML single sign-on, authorise your token for
that organisation once, from the browser page GitHub links in the error, or with:

```sh
gh auth refresh
```

A protected branch may also require a review from a code owner or a second approval. An approval
from `/pr-review` counts as yours, and it does not bypass any branch rule.
