"""Result models and JSON Schema export."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

OUTPUT_SCHEMA_VERSION = 1


class ExtractionResult(BaseModel):
    citefield_version: str
    output_schema_version: int = OUTPUT_SCHEMA_VERSION

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2), encoding="utf-8")
