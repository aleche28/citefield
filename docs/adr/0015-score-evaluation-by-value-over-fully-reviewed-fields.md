# 0015. Score the evaluation by value, over fully reviewed fields only

- Status: Accepted
- Date: 2026-10-31

## Context

The design defines the golden set (accepted, edited and added values are positives, rejected values negatives) and the metrics, but not how a new prediction is matched to a reviewed value, what to do with predictions nobody has judged, or how to count an edited value's original ([design.md, Review, re-extraction and evaluation](../design.md#review-re-extraction-and-evaluation)). The first evaluation slice exists to show whether `evidence_match` can be trusted on real manuals, so the rules must keep precision honest with a small, partly reviewed golden set.

## Considered options

Matching key:

- **Field, normalized value and normalized context**: the same key as `value_id`, but contexts are free text from the model ("MEP-803A" vs "model MEP-803A"), so equal values would miss on wording.
- **Field and normalized value only**, with context differences counted separately: robust to wording, but blind to a right value given for the wrong variant.

Predictions that match no reviewed value:

- **Count only predictions that match a reviewed value**: easy, but overstates precision.
- **Score a field only once it is fully reviewed**, and count every unmatched prediction in it as a false positive: honest, at the cost of skipping fields with pending values.

An edited value's original: count it as a negative, or ignore it.

## Decision

We will match on field and normalized value (the reviewed value for an edited one), and report true positives whose contexts differ as `context_mismatches`. A field counts in a document only when it has no pending values and has at least one reviewed value or is confirmed absent. In such a field, every prediction that matches no positive is a false positive; the ones that match no negative either are listed as unjudged, so the reviewer can add them to the golden set. The original of an edited value is a negative. Accuracy by signal range covers `evidence_match` and `model_confidence` in three ranges (below 0.5, 0.5 to 0.85, 0.85 and above), plus null.

## Consequences

- A value given for the wrong variant still scores as correct; `context_mismatches` shows how often contexts differ, which feeds the open question on merge context matching. Revisit when that question is answered.
- Reviewers must finish a field to have it count.
- A correct unjudged prediction can be reviewed into the golden set as an added value. A wrong one has no way in yet: added values are always positives, and the prediction's `value_id` is not in the golden output, so a decision can't reject it. Until there is one, the same wrong value is listed as unjudged on every run; this is an open question in design.md.
- The other signals (`citation_count`, `run_agreement`, `unit_resolved`) are not scored yet.
