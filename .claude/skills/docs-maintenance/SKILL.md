---
name: docs-maintenance
description: Keep citefield's docs/ organized and in sync with the code. Use when adding, moving, renaming or deleting a doc; when the user asks where a doc should go or to tidy up the docs; and before finishing a code change that affects user-visible behaviour - the output JSON, confidence signals, config schema, CLI commands or flags, public API, plugin protocols, dependencies or v1 scope - to check whether docs/design.md, the README or an ADR need updating.
---

# Docs maintenance

`docs/README.md` is the map of the docs. Read it first.

## Where things go

| Content                                                  | Location                                                  |
| -------------------------------------------------------- | --------------------------------------------------------- |
| How the system works now: architecture, contracts, API   | `docs/design.md` (one doc; split it only if the user asks) |
| Why a decision was made, and the options we rejected     | `docs/adr/`, via the `adr` skill                          |
| Task-oriented how-tos for users                          | `docs/guides/<task>.md`                                   |
| Exhaustive reference: config schema, CLI, output JSON    | `docs/reference/<topic>.md`, generated from code if possible |
| Project pitch, install, quick start                      | `README.md` at the repo root                              |
| Instructions for agents working in the repo             | `CLAUDE.md` and `.claude/skills/`                         |

Create `guides/` or `reference/` only when the first doc for it exists, and add the folder to the table in `docs/README.md` at the same time.

File names are lowercase kebab-case `.md`. Every doc starts with one `#` heading and is linked from `docs/README.md` or from an index that page links to. Docs that nothing links to get lost.

## After a code change

Check each of these and update what's affected, in the same change as the code:

1. **design.md**: does it still describe what the code does? Update the section; don't add a changelog to it.
2. **ADR**: did the change make or reverse a decision (see the `adr` skill for what counts)? If so, write or supersede an ADR.
3. **README.md**: do the examples, status line or install instructions still hold?
4. **Contracts**: a change to signals or output JSON also needs `output_schema_version` and the versioning rules in ADR-0006 respected.

If none apply, say so in one line; don't touch docs for the sake of it.

## Moving or renaming a doc

Use `git mv`, then search for links to the old path (`grep -rn "old-name" --include=*.md .`) and update them. Never renumber or rename an ADR file.

## Finish

Run `uv run python scripts/check_docs.py` (add `--write` if the ADR index changed) and fix everything it reports. Report which docs changed and why.
