# 0010. Reuse the workshop's ideas, not its code

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#acknowledgements-and-licensing) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

citefield's design is inspired by Luca Bianchi's workshop _Documents Are Not Knowledge_ (Codemotion Milan 2026). The workshop's [companion repository](https://github.com/aletheia/codemotion2026-km-harness-workshop) carries no license (checked 30 Oct 2026), so its contents can't be redistributed under Apache 2.0.

## Considered options

Not recorded; backfilled from design.md v1.0.0.

## Decision

citefield reuses ideas, not code: the LLM only proposes and humans verify; reconfirmation, novelty and conflict on re-extraction; golden sets built from human decisions; prompt examples excluded from evaluation. No code, prompts, fixtures or text are copied from the workshop repository, and the inspiration is credited in the README and design doc.

## Consequences

- If code is ever ported from the workshop, it needs a license or the author's written permission first, and a new ADR that supersedes this one.
