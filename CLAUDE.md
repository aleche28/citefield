# citefield

Python library and CLI that extracts metadata from technical manuals, with a verified citation for every value. Early stage: the modules in `src/citefield/` are stubs that follow `docs/design.md`.

## Commands

- `uv run python -m pytest`: tests, including the docs check
- `uv run ruff check` and `uv run ruff format`: lint and format
- `uv run python scripts/check_docs.py [--write]`: check docs; `--write` regenerates the ADR index

## Docs

- `docs/design.md` describes the current design; `docs/adr/` records why. ADRs are append-only: supersede, don't rewrite.
- Use the `adr` skill to record or supersede a decision, and the `docs-maintenance` skill when adding or moving docs or after a change to a public contract, dependency or scope.
- Run the docs check before committing doc changes.
