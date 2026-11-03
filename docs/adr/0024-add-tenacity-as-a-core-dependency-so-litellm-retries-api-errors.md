# 0024. Add tenacity as a core dependency, so LiteLLM retries API errors

- Status: Accepted
- Date: 2026-11-03

## Context

The LiteLLM backend passes `settings.llm.max_retries` to LiteLLM as `num_retries`, so that the backend retries transient API errors and the core doesn't ([design.md, Extraction pipeline](../design.md#extraction)). On an API error LiteLLM hands the call to a retry wrapper that imports `tenacity`, which LiteLLM doesn't declare as a dependency. Without it, every API error became `Exception: tenacity import failed`: transient errors were never retried, and the real error, such as a rejected parameter, was lost. Found on 2026-11-03 with LiteLLM 1.106.6 while working on [ADR-0023](0023-add-a-model-flag-and-check-the-provider-setup-before-the-first-call.md).

## Considered options

- **Add `tenacity`** (Apache-2.0, pure Python, no dependencies of its own): LiteLLM's retries work as documented. They also retry client errors, such as a rejected parameter, before giving up.
- **Stop passing `num_retries`** and rely on each provider SDK's own retries: no new dependency, but not every LiteLLM provider goes through an SDK with retries.
- **Retry in citefield's backend**: full control over what is retried, but more code for something LiteLLM already does.

## Decision

We will add `tenacity` to the core dependencies and keep passing `num_retries`.

## Consequences

- Transient API errors are retried, and the error that remains is the provider's own.
- A request the provider rejects is sent `max_retries` more times before failing; with the default of 2, that's two wasted calls, which cost nothing when they are rejected.
- If LiteLLM starts declaring `tenacity` itself, the entry can go.
