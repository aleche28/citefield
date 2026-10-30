# 0006. Expose named confidence signals, without an aggregate score

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#evidence-and-confidence-signals) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

Reviewers and client applications need to know how much to trust each value. Different clients weigh evidence differently, and in v1 there is no data yet to fit weights.

## Considered options

Not recorded; backfilled from design.md v1.0.0.

## Decision

We will attach a set of named signals to each value (`evidence_match`, `citation_count`, `run_agreement`, `model_confidence`, `unit_resolved`) and no aggregate score or band. Clients decide how to weigh them. Signals are an object keyed by name, so clients read them by name rather than by position.

Signal names and semantics are public API: adding a signal is a minor version; renaming, removing or changing a range is a major version. `output_schema_version` lets clients check what they read.

## Consequences

- Every client has to choose its own thresholds; `citefield eval` reports accuracy by signal range to help.
- An optional helper that fits weights on the golden set is on the roadmap, outside the core.
- Changing the signal set or semantics needs a new ADR, because it is a contract change.
