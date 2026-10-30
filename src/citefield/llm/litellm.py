"""Default backend: LiteLLM, covering cloud APIs and local servers (Ollama, vLLM)."""

from __future__ import annotations

from pydantic import BaseModel

from citefield.llm.base import Message


class LiteLLMBackend:
    name = "litellm"

    def __init__(self, model: str) -> None:
        self.model = model

    @property
    def context_window(self) -> int:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        raise NotImplementedError

    def complete_structured(self, messages: list[Message], schema: type[BaseModel]) -> BaseModel:
        raise NotImplementedError
