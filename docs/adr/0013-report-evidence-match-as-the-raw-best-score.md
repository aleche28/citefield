# 0013. Report evidence_match as the raw best score, and flag weak evidence with a warning

- Status: Accepted
- Date: 2026-10-30

## Context

The design defined `evidence_match` as the best match of the cited evidence on the cited page ±`page_window`, "0 if nothing matched", and had a `fuzzy_min_ratio` setting (0.85) without saying how the two relate ([design.md, Evidence and confidence signals](../design.md#evidence-and-confidence-signals)). Signal semantics are public API ([ADR-0006](0006-named-confidence-signals-without-aggregate-score.md)), so the reading has to be fixed. The first runs on the corpus produced quotes that the model had "repaired" from garbled PDF text, scoring between 0 and the threshold.

## Considered options

- **Below `fuzzy_min_ratio`, report 0**: one clear cut-off for "verified", but it hides how close the quote was, and the evaluation's accuracy by signal range would see nothing between 0 and the threshold.
- **Always report the raw best score; use `fuzzy_min_ratio` only for a warning**: the signal keeps its information, and clients choose their own threshold, as ADR-0006 intends.

## Decision

We will report `evidence_match` as the raw best score, 0 only when nothing matched at all. `fuzzy_min_ratio` no longer changes the signal: a value whose best `evidence_match` is below it gets an `evidence_not_verified` warning in the output.

## Consequences

- Clients and the evaluation see the full range of the signal, so `citefield eval` can show where a useful threshold lies.
- A client that wants a hard cut-off applies its own threshold, or reads the warnings.
- Changing the default `fuzzy_min_ratio` changes warnings, not values or signals.
