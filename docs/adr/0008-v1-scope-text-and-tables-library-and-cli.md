# 0008. Limit v1 to text and tables, as a library and CLI

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#scope) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

citefield's core value is extraction with verifiable evidence. Everything else should wait until v1 has run on real manuals.

## Considered options

Not recorded; backfilled from design.md v1.0.0.

## Decision

v1 is a synchronous library plus a thin CLI, for PDF and Markdown, covering extraction, verification, merging, proposals, review carry-over and evaluation. Out of scope for v1:

- a review UI (the core ships `apply_review`; collecting decisions is up to the client)
- diagrams and scanned pages: no vision, no OCR (low-text pages are reported as warnings)
- filling values from the model's world knowledge
- storing results in a database
- retrieval for very large documents

## Consequences

- Manuals that are mostly scanned or visual get little out of v1; the `low_text_units` warning makes that visible.
- Each item on the roadmap table in `design.md` needs an ADR when it moves into scope.
