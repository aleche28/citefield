# 0017. Match evaluation values on a looser key, and accept equivalent forms the reviewer declares

- Status: Accepted
- Date: 2026-10-31
- Supersedes: ADR-0015

## Context

[ADR-0015](0015-score-evaluation-by-value-over-fully-reviewed-fields.md) matches a prediction to a golden value on field and normalized value, where normalized means case- and whitespace-folded text ([design.md, Review, re-extraction and evaluation](../design.md#review-re-extraction-and-evaluation)). The first model bake-off ran four models on the corpus and scored them against a golden set reviewed from one model's output. Most of the other models' "false positives" were the same values written differently: `18.92lb` against a golden value `18.92` with unit `lb`, `Genuine ANTCLABS BLTouch®` against `Genuine ANTCLABS BLTouch`, `5° C to 32° C (41° F to 113° F)` against `5° C to 32° C`, and the build volume in millimetres against the same volume in inches, both stated in the manual. The ranking measured which model wrote like the reviewed one, not which model was right. Every field in the example configs is a string, so unit parsing for numbers doesn't help.

## Considered options

Formatting differences:

- **Loosen `value_key`**, which also drives `value_id` and merging: one notion of sameness, but it changes every `value_id`, breaking the decisions files keyed by them.
- **A separate, looser key used only by the evaluation**: `value_id` and merging stay as they are.

Differences of wording or unit that no normalization can fold:

- **Review the variants in as added values**: no schema change, but each would be a separate positive, so a model that gives one form misses the other.
- **Equivalent forms on a reviewed value, in the output's `review`**: one positive matched by any of its forms. An additive change to the output JSON, consistent with [ADR-0007](0007-store-reviews-in-the-output-file.md).
- **An evaluation-only sidecar file in the golden folder**: no schema change, but the golden truth is split across two files and isn't carried over on re-extraction.

How strict equivalence is: **same wording** (only formatting, units the manual states, conversions, trademarks and footnote marks) rewards concise values; **same fact** also accepts marketing words and extra detail of the same fact from the same passage, and measures whether the model found the right fact.

## Decision

We will match on field and a match key used only by the evaluation: the text casefolded, without whitespace, ®, ™ or ©, with curly quotes straightened and trailing footnote asterisks removed. For a string field, a value's `raw_unit` is appended when the value doesn't already end with it. The same key applies to positives, negatives, the `examples` exclusion and predictions.

A reviewer can declare equivalent forms on an accepted, edited or added value, written with `also_accept` in the decisions file and stored as `review.equivalents`. A prediction matching any form of a positive matches that positive; several predictions matching the same positive count as one true positive, and a positive no prediction matches is a false negative. An equivalent that matches another positive or a negative is an error.

Equivalence means the same fact. A form is equivalent if it states the same fact as the reviewed value, differing only in notation, a unit or conversion the manual states, trademark or marketing words, footnote marks, or extra detail of the same fact taken from the same passage. A different, partial or garbled claim is not equivalent.

Everything else in ADR-0015 stands: context is not part of the match and differences are counted as `context_mismatches`, only fully reviewed fields count, unmatched predictions in them are false positives and those matching no negative are listed as unjudged, the original of an edited value is a negative, and signals are scored by range.

## Consequences

- Correct values in another form no longer count against a model, so the bake-off can compare models on a golden set reviewed from one of them, once the variants are reviewed in.
- `review.equivalents` is optional and defaults to empty, so existing outputs still load and `output_schema_version` stays 1.
- A prediction missing a unit the golden value states no longer matches it: bare `18.92` doesn't match `18.92` with unit `lb`, as it did under ADR-0015.
- Equivalence is a reviewer judgement. The rule above has to be applied to every model's variants the same way, from the manual's text rather than from which model wrote them.
- The looser key can merge two values that differ only in spacing or a trademark sign. That's intended for scoring, but it isn't used for `value_id` or merging, so the output can still hold both.
- A wrong unjudged prediction still can't become a negative: that open question in design.md is unchanged.
