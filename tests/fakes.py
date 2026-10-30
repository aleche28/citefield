"""Test doubles: an LLM backend that replays canned responses."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from citefield.llm.base import Completion, Message

Response = str | dict[str, Any] | Exception


class FakeBackend:
    """Replays responses in order. A dict or str is validated against the schema like a real
    model answer; an exception is raised."""

    name = "fake"

    def __init__(self, *responses: Response, context_window: int = 100_000) -> None:
        self.responses = list(responses)
        self.context_window = context_window
        self.calls: list[list[Message]] = []

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def complete_structured(self, messages: list[Message], schema: type[BaseModel]) -> Completion:
        self.calls.append(messages)
        if not self.responses:
            raise AssertionError("FakeBackend ran out of responses")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        text = response if isinstance(response, str) else json.dumps(response)
        return Completion(
            parsed=schema.model_validate_json(text), input_tokens=100, output_tokens=10
        )


def answer(name: str, *candidates: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "candidates": list(candidates)}


def candidate(
    raw_value: str,
    *quotes: tuple[int, str],
    context: str | None = None,
    raw_unit: str | None = None,
    confidence: float = 0.9,
) -> dict[str, Any]:
    return {
        "raw_value": raw_value,
        "raw_unit": raw_unit,
        "context": context,
        "evidence": [{"page": page, "quote": quote} for page, quote in quotes],
        "model_confidence": confidence,
    }
