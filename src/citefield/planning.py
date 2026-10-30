"""Token counts, chunks and field batches."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from citefield.config import ChunkingSettings, FieldDef
from citefield.llm.base import LLMBackend, Message
from citefield.parsers.base import ParsedDocument
from citefield.prompts import extract_v1

# Tokens kept free for the model's answer when max_input_tokens is "auto".
OUTPUT_RESERVE_TOKENS = 8_192


class DocumentTooLarge(Exception):
    """The document doesn't fit in one chunk, and chunking isn't implemented yet."""


@dataclass
class Batch:
    """One extraction call: its fields and the exact messages that were budgeted."""

    fields: list[FieldDef]
    messages: list[Message]
    prompt_tokens: int


@dataclass
class Plan:
    chunks: int
    batches: list[Batch]
    document_tokens: int
    input_budget: int
    n_runs: int = 1

    @property
    def max_prompt_tokens(self) -> int:
        return max((b.prompt_tokens for b in self.batches), default=0)

    @property
    def calls(self) -> int:
        return self.chunks * len(self.batches) * self.n_runs


def batch_fields(fields: Sequence[FieldDef], size: int) -> list[list[FieldDef]]:
    if size < 1:
        raise ValueError("field_batch_size must be at least 1")
    return [list(fields[i : i + size]) for i in range(0, len(fields), size)]


def input_budget(chunking: ChunkingSettings, context_window: int) -> int:
    if chunking.max_input_tokens == "auto":
        return context_window - OUTPUT_RESERVE_TOKENS
    return chunking.max_input_tokens


def make_plan(
    document: ParsedDocument,
    fields: Sequence[FieldDef],
    backend: LLMBackend,
    *,
    chunking: ChunkingSettings,
    batch_size: int,
    n_runs: int = 1,
) -> Plan:
    """Plan the extraction calls. The whole document goes in one chunk for now."""
    text = extract_v1.render_units(document.units)
    batches = []
    for batch in batch_fields(fields, batch_size):
        messages = extract_v1.build_messages(batch, text)
        tokens = backend.count_tokens("\n\n".join(m.content for m in messages))
        batches.append(Batch(fields=batch, messages=messages, prompt_tokens=tokens))
    plan = Plan(
        chunks=1,
        batches=batches,
        document_tokens=backend.count_tokens(text),
        input_budget=input_budget(chunking, backend.context_window),
        n_runs=n_runs,
    )
    if plan.max_prompt_tokens > plan.input_budget:
        raise DocumentTooLarge(
            f"{document.path}: the prompt needs {plan.max_prompt_tokens} tokens, over the "
            f"input budget of {plan.input_budget}; chunking large documents isn't supported yet"
        )
    return plan
