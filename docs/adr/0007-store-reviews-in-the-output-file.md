# 0007. Store reviews in the output file and carry them over

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#review-re-extraction-and-evaluation) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

Human review is the expensive part of the workflow. Re-running extraction (new config, model, parser or manual revision) must not throw that work away, and reviewed values are the best available evaluation data.

## Considered options

- **Review fields in the per-document output JSON, carried over with `--previous`**: no extra storage; one file per document.
- **Append-only event log for re-ingestion**, in the style of the workshop: keeps full history, but adds storage and tooling.

## Decision

We will write review decisions into the output JSON itself. Every value has empty review fields from the start. On re-extraction with `--previous`, reviews are carried over by `document_id` and `value_id` (reconfirmation, novelty, conflict, re-proposed rejection), and values the reviewer added are kept. The golden set for evaluation is every reviewed value across a folder of outputs.

## Consequences

- No database in v1; history is the previous output file per document.
- Reconfirmation assumes the first reviewer was right; audit sampling of carried-over values is planned for later.
- The append-only event log stays on the roadmap; adopting it would supersede this ADR.
