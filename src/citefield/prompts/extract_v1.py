"""Extraction prompt, version extract-v1, and the response schema the LLM fills in."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

from citefield.config import FieldDef
from citefield.llm.base import Message
from citefield.parsers.base import Unit

VERSION = "extract-v1"

SYSTEM = """\
You extract metadata from a technical manual. You only propose values; code checks every \
citation against the document afterwards.

Rules:
1. Use only the manual text below. Never use outside knowledge, and never guess.
2. Every value needs evidence: a quote copied verbatim from the text, with the page number \
from the nearest [[page N]] marker before it. Keep quotes short: the sentence or table line \
that states the value.
3. Copy raw_value and raw_unit verbatim, as written in the manual. Don't convert, round, \
translate or reformat them. raw_unit is null when the field has no unit or none is written.
4. For an enum field, raw_value must be one of the field's allowed values, and the quote \
must be the text that supports that choice.
5. context says what the value applies to (a model, variant, format or condition), copied \
from the text; null when the text doesn't qualify the value.
6. If a value is stated more than once, return one candidate with all its quotes. If \
different values apply to different contexts, return one candidate per context.
7. If the manual doesn't state a field, return it with an empty candidates list.
8. model_confidence is your own estimate, from 0 to 1, that the value is right for the field.
9. Answer every requested field, using its exact name.
"""


class QuoteRef(BaseModel):
    page: int
    quote: str


class Candidate(BaseModel):
    raw_value: str
    raw_unit: str | None
    context: str | None
    evidence: list[QuoteRef]
    model_confidence: float


class FieldAnswer(BaseModel):
    name: str
    candidates: list[Candidate]


class ExtractResponse(BaseModel):
    fields: list[FieldAnswer]


def render_units(units: Sequence[Unit]) -> str:
    """Document text with explicit page markers, as the LLM sees it."""
    parts = []
    for unit in units:
        marker = f"[[page {unit.locator.page}]]" if unit.locator.page else f"[[{unit.id}]]"
        parts.append(f"{marker}\n{unit.text.strip()}")
    return "\n\n".join(parts)


def render_field(field: FieldDef) -> str:
    lines = [
        f"- name: {field.name}",
        f"  type: {field.type}",
        f"  description: {field.description}",
    ]
    if field.unit:
        lines.append(f"  unit: {field.unit}")
    if field.values:
        lines.append(f"  allowed values: {', '.join(field.values)}")
    if field.aliases:
        lines.append(f"  also called: {', '.join(field.aliases)}")
    if field.examples:
        lines.append(f"  examples: {'; '.join(field.examples)}")
    return "\n".join(lines)


def build_messages(fields: Sequence[FieldDef], document_text: str) -> list[Message]:
    field_block = "\n".join(render_field(f) for f in fields)
    user = (
        f"Fields to extract:\n{field_block}\n\nManual text:\n<manual>\n{document_text}\n</manual>"
    )
    return [Message(role="system", content=SYSTEM), Message(role="user", content=user)]
