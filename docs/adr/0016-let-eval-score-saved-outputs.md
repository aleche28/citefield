# 0016. Let eval score saved outputs as well as extract again

- Status: Accepted
- Date: 2026-10-31

## Context

The design says `citefield eval` re-runs extraction on the golden documents with the current config ([design.md, Review, re-extraction and evaluation](../design.md#review-re-extraction-and-evaluation)). The model bake-off that follows the first evaluation slice compares several models on the same golden set, and the scoring rules will change while the golden set grows. Re-running extraction for every scoring change costs API calls and adds model variance. Re-running also needs the manual, found at the path recorded in the golden output, which only holds on the machine and directory it was made from.

## Considered options

- **Re-run only**, as designed: one way to evaluate, but every scoring change costs a run.
- **Re-run by default, or score a folder of saved outputs** with `--predictions`: outputs from `citefield extract` can be scored many times for free.

## Decision

We will keep re-running as the default and add `--predictions DIR` to score saved outputs, paired with the golden outputs by `document_id` and checked by SHA-256. When re-running, the manual is found at its recorded path, or by SHA-256 in `--documents DIR`, and a file whose hash differs is refused. `evaluate()` takes the same options, plus an `extractor` argument so callers and tests can pass their own backend.

## Consequences

- A bake-off is `citefield extract` once per model, then `eval --predictions` per output folder.
- `eval --json` writes the report, with each prediction's model, prompt version, settings hash and tokens, so reports from different runs can be compared.
- The public API of `evaluate()` grows three keyword arguments.
