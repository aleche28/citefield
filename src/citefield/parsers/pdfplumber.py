"""Default PDF parser, installed with the core package."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber

from citefield.parsers.base import Locator, ParsedDocument, ParserInfo, Unit

# Pages with fewer non-whitespace characters are flagged low_text: blank, scanned or mostly
# visual (figures, decals, chapter dividers).
LOW_TEXT_MIN_CHARS = 200


class PdfplumberParser:
    name = "pdfplumber"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> ParsedDocument:
        path = Path(path)
        units = []
        with pdfplumber.open(path) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                page.close()  # free the page's layout objects; they add up on long manuals
                units.append(
                    Unit(
                        id=f"p{number}",
                        locator=Locator(page=number),
                        text=text,
                        low_text=len("".join(text.split())) < LOW_TEXT_MIN_CHARS,
                    )
                )
        with path.open("rb") as f:
            sha256 = hashlib.file_digest(f, "sha256").hexdigest()
        return ParsedDocument(
            path=str(path),
            sha256=sha256,
            parser=ParserInfo(name=self.name, version=pdfplumber.__version__),
            units=units,
        )
