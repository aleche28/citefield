"""Built-in Markdown reader: splits the document by headings."""

from __future__ import annotations

from pathlib import Path

from citefield.parsers.base import ParsedDocument


class MarkdownParser:
    name = "markdown"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".markdown"}

    def parse(self, path: Path) -> ParsedDocument:
        raise NotImplementedError
