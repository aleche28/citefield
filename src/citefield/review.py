"""Apply review decisions, and carry reviews over on re-extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from citefield.output import ExtractionResult


def apply_review(output: str | Path | ExtractionResult, decisions: Any) -> ExtractionResult:
    raise NotImplementedError
