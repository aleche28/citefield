# 0003. Require evidence for every value, verified in code

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#overview) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

LLMs are good at finding values in long documents and bad at proving where those values came from. citefield's output is meant to be reviewed value by value, so each value has to be traceable to the manual.

## Considered options

Not recorded; backfilled from design.md v1.0.0.

## Decision

We will keep the LLM's job narrow: the LLM only proposes, code verifies, humans decide.

- Every value cites a verbatim quote or a table cell and its page. A candidate without evidence is not a value.
- Code checks that the cited evidence appears in the parsed document and reports how well it matched (`evidence_match`).
- Unit conversion, number parsing, evidence checks and merging are deterministic code, not prompts.
- Conflicting values are kept for the reviewer and never resolved silently.
- The model never fills values from its own world knowledge.

## Consequences

- Fields that a manual doesn't state stay `not_found`, even when the model could guess them.
- `evidence_match` depends on the parser's text quality, so it is best-effort in v1 (see [ADR-0004](0004-pdfplumber-as-default-parser-with-optional-extras.md)).
- Prompts must ask for verbatim raw values and units, and the post-processing code owns every transformation from raw to canonical.
