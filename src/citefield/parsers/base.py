"""Parser protocol and the internal document model every parser returns."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class Locator(BaseModel):
    page: int | None = None  # PDF
    section: str | None = None  # Markdown, e.g. "3.2 Technical data"


class ParserInfo(BaseModel):
    name: str
    version: str


class Table(BaseModel):
    id: str  # e.g. "t3"
    locator: Locator
    header: list[list[str]]
    rows: list[list[str]]


class Unit(BaseModel):
    id: str
    locator: Locator
    text: str
    tables: list[Table] = []
    low_text: bool = False  # little extractable text: likely scanned or visual


class ParsedDocument(BaseModel):
    path: str
    sha256: str
    parser: ParserInfo
    units: list[Unit]  # pages for PDF, heading sections for Markdown


class DocumentParser(Protocol):
    name: str

    def supports(self, path: Path) -> bool: ...

    def parse(self, path: Path) -> ParsedDocument: ...
