# 0014. Record field-level review in the output, as a review object on each field

- Status: Accepted
- Date: 2026-10-31

## Context

The design lets a reviewer confirm that a `not_found` field is really absent from the manual (review status `confirmed_absent`), and the evaluation scores `not_found` accuracy against those fields ([design.md, Review, re-extraction and evaluation](../design.md#review-re-extraction-and-evaluation)). The output JSON had no place for it: review fields existed only on values. Values the reviewer adds also need signals, because `Signals` is required on every value and `evidence_match` is never null ([ADR-0006](0006-named-confidence-signals-without-aggregate-score.md)); evidence is verified in code ([ADR-0003](0003-require-evidence-for-every-value-verified-in-code.md)).

## Considered options

- **A `review` object on each field** (`status` `pending` or `confirmed_absent`, `reviewer`, `reviewed_at`, `note`), defaulting to `pending`. It matches the value-level `review`, and files written before it still load.
- **Leave `not_found` accuracy out of the first evaluation**: no output change, but the evaluation can't tell a correct `not_found` from a missed value.

## Decision

We will add a `review` object to every field result, with status `pending` or `confirmed_absent`. `apply_review` writes it; a field can be confirmed absent only when all its values are rejected. A value the reviewer adds has its evidence verified like any other: `apply_review` takes the document's page texts and computes `evidence_match`, which is 0 without them. Its `model_confidence` is null.

## Consequences

- `output_schema_version` stays 1: the new object is optional with a default, so existing files and clients keep working. It is an addition to the output contract.
- A reviewer's typo in an added quote shows up as a low `evidence_match`; `scripts/review.py` parses the manual for this and warns below `fuzzy_min_ratio`.
- Re-extraction (carry-over) must also carry `confirmed_absent` over, and drop it when the new run finds a value for the field.
