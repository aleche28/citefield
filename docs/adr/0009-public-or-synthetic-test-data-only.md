# 0009. Use only public or synthetic manuals as test data

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#acknowledgements-and-licensing) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

Realistic test data for citefield is technical manuals, many of which are proprietary. The repository is public and Apache 2.0 licensed.

## Considered options

Not recorded; backfilled from design.md v1.0.0.

## Decision

The repository contains only public or synthetic manuals. No proprietary documents, not even as test fixtures.

## Consequences

- Fixtures and evaluation sets must come from public manuals or be synthetic.
- Evaluation on proprietary manuals happens outside the repository.
