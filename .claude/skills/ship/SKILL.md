---
name: ship
description: Finish the current branch and open a pull request - simplify the branch's changes, run lint, tests and the docs check, push and create the PR.
disable-model-invocation: true
---

# Ship a branch

Takes a finished branch to an open PR against `main`. The user typed /ship, so push and create it without asking again, but stop and report if a step below says to.

## 1. Check the branch

1. If the current branch is `main`, stop and ask for a branch name.
2. Run `git fetch origin main` and use `origin/main` as the base.
3. If `git status` shows uncommitted changes, list them and ask whether they belong in this PR. Commit them only if the user says yes.
4. If `git log origin/main..HEAD` is empty, there is nothing to ship: say so and stop.

## 2. Simplify

Invoke the `simplify` skill on the branch's changes vs `origin/main` (`git diff origin/main...HEAD`), not just the uncommitted ones.

Review what it changed. Keep cleanups. Revert any edit that changes behaviour, the output JSON, the config schema, the CLI or the public API, and mention it in the report. If something is left, commit it on its own as `refactor: simplify <what>`. If it found nothing, say so and move on.

## 3. Check

Run these, in order, and fix what they report:

```sh
uv run ruff format
uv run ruff check
uv run pytest
uv run python scripts/check_docs.py
```

Commit formatting and lint fixes. If a test fails and the fix isn't obvious and local, stop and report the failure; don't open the PR.

If the branch changes a public contract, a dependency or the v1 scope, follow the `docs-maintenance` skill before going on.

## 4. Open the PR

1. `git push -u origin HEAD`.
2. `gh pr create --base main` with:
   - **Title**: Conventional Commits style, like the commit history (`feat: …`, `fix: …`, `docs: …`), under 70 characters.
   - **Body**: a `## Summary` saying what changed and why, grouped by file or area where that helps, with ADR numbers for any decisions; what was left out on purpose, if anything. Then a `## Test plan` checklist: ticked items for what you ran in step 3, unticked ones for what only CI or the reviewer can check.

## Report

Give the PR URL, what simplify changed (or that it changed nothing), anything you reverted and why, and the check results.
