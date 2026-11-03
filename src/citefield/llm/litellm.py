"""Default backend: LiteLLM, covering cloud APIs and local servers (Ollama, vLLM)."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel

from citefield.llm.base import Completion, Message, UnsupportedSettingError

# Used when LiteLLM doesn't know the model's context window; set
# `settings.chunking.max_input_tokens` to override it.
DEFAULT_CONTEXT_WINDOW = 128_000

# LiteLLM's validate_environment doesn't know azure_ai/, and asks azure/ for an API version
# it has a default for. Each prefix needs its endpoint, and a key unless Entra ID is set up.
_AZURE = {
    "azure_ai/": ("AZURE_AI_API_BASE", "AZURE_AI_API_KEY"),
    "azure/": ("AZURE_API_BASE", "AZURE_API_KEY"),
}
_ENTRA_ID = ("AZURE_AD_TOKEN", "AZURE_CLIENT_ID")

# OpenRouter's answer when require_parameters leaves no provider for the request.
_NO_OPENROUTER_ENDPOINT = "No endpoints found that can handle the requested parameters"


def check_environment(model: str) -> tuple[list[str], list[str]]:
    """Problems and warnings about the environment variables `model` needs, without a call.

    Providers LiteLLM can't check pass, and fail at the first call instead.
    """
    if model.startswith(("ollama/", "ollama_chat/")):
        if os.environ.get("OLLAMA_API_BASE"):
            return [], []
        return [], [f"OLLAMA_API_BASE is not set for {model}; using http://localhost:11434"]
    for prefix, (base, key) in _AZURE.items():
        if model.startswith(prefix):
            problems = [] if os.environ.get(base) else [f"{base} is not set for {model}"]
            if not any(os.environ.get(name) for name in (key, *_ENTRA_ID)):
                problems.append(f"{key} is not set for {model} (or AZURE_AD_TOKEN for Entra ID)")
            return problems, []

    import litellm

    quiet = litellm.suppress_debug_info
    litellm.suppress_debug_info = True  # an unknown provider prints LiteLLM's provider list
    try:
        missing = litellm.validate_environment(model)["missing_keys"]
    finally:
        litellm.suppress_debug_info = quiet
    if not missing:
        return [], []
    verb = "is" if len(missing) == 1 else "are"
    return [f"{', '.join(missing)} {verb} not set for {model}"], []


class LiteLLMBackend:
    name = "litellm"

    def __init__(
        self,
        model: str,
        temperature: float | None = 0,
        num_retries: int = 2,
        *,
        reasoning_effort: str | None = None,
        provider: dict[str, Any] | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.num_retries = num_retries  # transient API errors; invalid output is retried upstream
        self.reasoning_effort = reasoning_effort
        self.provider = provider  # OpenRouter provider routing preferences

    @property
    def context_window(self) -> int:
        import litellm

        try:
            info = litellm.get_model_info(self.model)
        except Exception:
            return DEFAULT_CONTEXT_WINDOW
        return info.get("max_input_tokens") or DEFAULT_CONTEXT_WINDOW

    def count_tokens(self, text: str) -> int:
        import litellm

        return litellm.token_counter(model=self.model, text=text)

    def complete_structured(self, messages: list[Message], schema: type[BaseModel]) -> Completion:
        import litellm

        kwargs: dict[str, Any] = {}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if self.model.startswith("openrouter/"):
            # Route only to providers that support every parameter we send, so a
            # structured-output request never lands on one that ignores the schema.
            provider = {"require_parameters": True, **(self.provider or {})}
            kwargs["extra_body"] = {"provider": provider}
        try:
            response = litellm.completion(
                model=self.model,
                messages=[m.model_dump() for m in messages],
                response_format=schema,
                num_retries=self.num_retries,
                **kwargs,
            )
        except (litellm.BadRequestError, litellm.NotFoundError) as exc:
            hint = self._rejected_setting(str(exc))
            if hint is None:
                raise
            raise UnsupportedSettingError(hint) from exc
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return Completion(
            parsed=schema.model_validate_json(content),
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )

    def _rejected_setting(self, error: str) -> str | None:
        """What to change when `error` says the model rejects a setting we sent, else None."""
        sent = [
            name
            for name, value in (
                ("temperature", self.temperature),
                ("reasoning_effort", self.reasoning_effort),
            )
            if value is not None
        ]
        named = [name for name in sent if name in error.lower()]
        if named:
            fixes = " or ".join(f"settings.llm.{name}: null" for name in named)
            return f"{self.model} doesn't accept {' or '.join(named)}; set {fixes}"
        if sent and _NO_OPENROUTER_ENDPOINT in error:
            # OpenRouter doesn't say which parameter no provider supports.
            fixes = " or ".join(f"settings.llm.{name}: null" for name in sent)
            return (
                f"no OpenRouter provider for {self.model} accepts {', '.join(sent)} with "
                f"structured output; try {fixes}"
            )
        return None
