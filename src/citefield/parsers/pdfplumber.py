"""Default PDF parser, installed with the core package."""

from __future__ import annotations

from pathlib import Path

from citefield.parsers.base import ParsedDocument


class PdfplumberParser:
    name = "pdfplumber"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> ParsedDocument:
        raise NotImplementedError
