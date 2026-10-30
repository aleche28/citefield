"""LLM calls, response validation and retries."""

from __future__ import annotations

from pathlib import Path

from citefield.config import Config
from citefield.output import ExtractionResult


class Extractor:
    """Runs extraction with the parser and LLM backend named in the config's settings."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def extract(self, path: str | Path) -> ExtractionResult:
        raise NotImplementedError

    def reextract(self, path: str | Path, previous: str | Path) -> ExtractionResult:
        """Re-run extraction and carry reviews over from a previous output."""
        raise NotImplementedError
