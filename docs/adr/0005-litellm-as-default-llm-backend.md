# 0005. LiteLLM as the default LLM backend, behind a protocol

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#public-api-and-cli) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

Users run citefield against different providers, including cloud APIs and local servers. Extraction needs structured output and token counting from whatever model is configured.

## Considered options

Not recorded; backfilled from design.md v1.0.0.

## Decision

We will define the LLM backend as a protocol (`LLMBackend`: `context_window`, `count_tokens`, `complete_structured`) and ship a default adapter built on **LiteLLM**, which covers cloud APIs and local servers (Ollama, vLLM) behind one interface. Backends register through the `citefield.llm_backends` entry point.

## Consequences

- Provider-specific code stays out of the core; adding a provider means writing a backend, not changing extraction.
- Token counting for arbitrary models is still an open question in `design.md` (LiteLLM's counter or a character heuristic).
- The model's own confidence is only available when the backend provides it, so `model_confidence` can be null.
