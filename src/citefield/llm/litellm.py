"""Default backend: LiteLLM, covering cloud APIs and local servers (Ollama, vLLM)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from citefield.llm.base import Completion, Message

# Used when LiteLLM doesn't know the model's context window; set
# `settings.chunking.max_input_tokens` to override it.
DEFAULT_CONTEXT_WINDOW = 128_000


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
        response = litellm.completion(
            model=self.model,
            messages=[m.model_dump() for m in messages],
            response_format=schema,
            num_retries=self.num_retries,
            **kwargs,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return Completion(
            parsed=schema.model_validate_json(content),
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )
