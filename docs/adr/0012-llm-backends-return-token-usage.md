# 0012. LLM backends return token usage with each structured response

- Status: Accepted
- Date: 2026-10-30

## Context

The output records the tokens a run used (`run.tokens`), and the evaluation and the model bake-off compare models on cost. In the [LLM backend protocol](../design.md#public-api-and-cli), `complete_structured` returned only the validated pydantic model, so a backend had no way to report usage. The protocol is a plugin contract (backends register through the `citefield.llm_backends` entry point), so changing it needs a record. No backend outside this repository exists yet.

## Considered options

- **Return a `Completion` with the parsed model and token counts**: one value per call, explicit, and safe when calls run in parallel. Every backend changes its return type.
- **Keep the return type and expose usage counters on the backend object**: no signature change, but state shared across calls breaks with `--workers` and is easy to forget in a third-party backend.
- **Count tokens in the core with `count_tokens`**: no protocol change, but it misses output tokens the model really produced and the provider's own counts.

## Decision

We will have `complete_structured` return a `Completion(parsed, input_tokens, output_tokens)`, with the token counts `None` when the backend doesn't report them. It still raises `pydantic.ValidationError` for a response that doesn't match the schema, so the core can retry.

## Consequences

- `run.tokens` reflects what the provider billed, which the model bake-off needs.
- Third-party backends implement the new return type; there are none yet, so nothing breaks.
- If backends later need to report more per call (cost, cached tokens, reasoning tokens), they go into `Completion` as optional fields, which is a minor change.
