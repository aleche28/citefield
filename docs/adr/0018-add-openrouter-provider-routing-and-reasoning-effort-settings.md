# 0018. Add OpenRouter provider routing and reasoning effort to the LLM settings

- Status: Accepted
- Date: 2026-10-31

## Context

The model bake-off compares small models through OpenRouter ([design.md, Configuration](../design.md#configuration)). Open-weight models such as DeepSeek V4.1 Flash and Qwen3.8 27B are served by 20 to 40 providers each, at quantizations from fp4 to bf16 and prices that differ by more than ten times. The backend sent only `require_parameters: true` as routing, so each call could land on a different endpoint, and neither quality nor cost was comparable across runs. DeepSeek was dropped from the first bake-off for that reason. Qwen3.8 27B also reasons by default, and the bake-off should measure it with reasoning on and off. Both need new config keys, which are part of the config schema.

## Considered options

- **A raw `extra_body` passthrough**: covers any provider option, but it's untyped, mixes routing with request parameters, and lets a config override `require_parameters` by accident.
- **A typed `provider` block for OpenRouter routing, and LiteLLM's `reasoning_effort`**: two narrow keys. LiteLLM maps `reasoning_effort` for each provider, so it isn't tied to OpenRouter.
- **Pin providers in the OpenRouter account settings**: no schema change, but it lives outside the repository, so a run can't be reproduced from its config.

## Decision

We will add two optional keys to `settings.llm`:

- `provider`: OpenRouter provider-routing preferences, sent as `provider` in the request body, merged over `require_parameters: true`. Allowed only for `openrouter/` models. An endpoint is pinned with its tag and no fallbacks, e.g. `{order: [deepinfra/bf16], allow_fallbacks: false}`.
- `reasoning_effort`: `none`, `minimal`, `low`, `medium`, `high` or `xhigh`, passed to LiteLLM. Null, the default, sends nothing and keeps the provider's default.

Both are part of `settings_hash`, but only when set, so hashes recorded before this change still match.

## Consequences

- A bake-off run is reproducible from its config: model, endpoint and reasoning mode.
- A pinned endpoint that goes down fails the call instead of falling back. That's intended for comparisons; production configs can leave `provider` unset.
- Checked on 2026-10-31 with LiteLLM 1.106: `reasoning_effort: none` turns Qwen3.8 27B's reasoning off (0 reasoning tokens, against 44 by default on a one-line prompt), and a call pinned to `deepinfra/fp8` was billed at that endpoint's price.
- Choosing a backend other than LiteLLM from the config is still an open question; these keys belong to the LiteLLM backend.
