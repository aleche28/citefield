"""LLM backend protocol."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMBackend(Protocol):
    name: str
    context_window: int

    def count_tokens(self, text: str) -> int: ...

    def complete_structured(
        self, messages: list[Message], schema: type[BaseModel]
    ) -> BaseModel: ...
