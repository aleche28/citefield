# 0023. Add a --model flag and check the provider's setup before the first call

- Status: Accepted
- Date: 2026-11-03

## Context

citefield reaches every provider through LiteLLM ([ADR-0005](0005-litellm-as-default-llm-backend.md)), but the example configs all name an OpenRouter model, so someone with an Anthropic or Azure key has to edit the config first. A missing key only showed up at the first call, after parsing, as a raw LiteLLM error. A setting the model doesn't accept, such as `temperature` on Claude Haiku 5.5, failed every field batch the same way, still wrote an output full of `error` fields and exited with status 0 ([design.md, Public API and CLI](../design.md#public-api-and-cli)). Issue [#22](https://github.com/aleche28/citefield/issues/22); a first adopter uses Anthropic and Azure AI Foundry.

## Considered options

- **Model override:** a `--model` flag, an environment variable, or editing the config. A flag is visible in the command and in shell history; an environment variable is invisible in a recorded command, so it is left out for now.
- **Setup check:** LiteLLM's `validate_environment`, or a call to the provider. The call costs money and time; `validate_environment` needs no network, but it doesn't know `azure_ai/`, wants an API version for `azure/` that LiteLLM has a default for, and reports Ollama's optional `OLLAMA_API_BASE` as missing.
- **Rejected settings:** LiteLLM's `drop_params`, which drops them silently, or stopping with the setting to change. Dropping changes the request without the config or the settings hash saying so.

## Decision

We will:

- Add `--model` to `extract` and `eval`. It replaces `settings.llm.model` in the loaded config, which is then validated again, so the output's `model` and `settings_hash` record the model used. `eval --predictions` makes no calls, so `--model` with it is an error. A config with OpenRouter `provider` routing fails validation with a non-OpenRouter `--model`, rather than having the routing dropped.
- Check the model's environment variables before parsing, in `--dry-run` too, and stop naming the variable: `ANTHROPIC_API_KEY is not set for anthropic/claude-haiku-5-5`. The check uses `validate_environment`, with citefield's own rules for Azure (the endpoint, plus the key unless an Entra ID variable is set) and a warning only for Ollama. Providers LiteLLM can't check pass and fail at the first call.
- Stop the run when the model rejects a setting we sent, with the setting to change: `… doesn't accept temperature; set settings.llm.temperature: null`. On OpenRouter, where the answer doesn't name the parameter, the hint names every setting sent. The backend raises `UnsupportedSettingError`; it isn't recorded as a field error.

## Consequences

- The examples run on any provider unchanged: `citefield extract … -c examples/generator.yaml --model anthropic/claude-haiku-5-5`.
- The check knows only environment variables. A key passed some other way, such as Azure's `DefaultAzureCredential` without `AZURE_CLIENT_ID`, is reported as missing; revisit if that happens.
- Recognising a rejected setting relies on the provider's error text naming it, or on OpenRouter's "no endpoints" answer. Any other error stays a field error, as before.
