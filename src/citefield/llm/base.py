"""LLM backend protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class Completion:
    """A validated structured response, with the token usage the backend reports."""

    parsed: BaseModel
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMBackend(Protocol):
    name: str
    context_window: int

    def count_tokens(self, text: str) -> int: ...

    def complete_structured(self, messages: list[Message], schema: type[BaseModel]) -> Completion:
        """Return the response validated against `schema`.

        Raises `pydantic.ValidationError` if the response doesn't match the schema, so the
        caller can retry.
        """
        ...
