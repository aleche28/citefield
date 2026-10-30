"""Evaluation against the golden set built from reviewed values."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from citefield.config import Config


def evaluate(outputs: str | Path, config: Config) -> Any:
    raise NotImplementedError
