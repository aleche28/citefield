"""Pydantic models for the YAML config, and the pint unit registry."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

FieldType = Literal["number", "integer", "string", "boolean", "enum", "date"]


class FieldDef(BaseModel):
    name: str
    description: str
    type: FieldType = "string"
    unit: str | None = None
    values: list[str] | None = None
    aliases: list[str] = []
    examples: list[str] = []


class LLMSettings(BaseModel):
    model: str | None = None
    temperature: float = 0
    max_retries: int = 2


class ChunkingSettings(BaseModel):
    max_input_tokens: int | Literal["auto"] = "auto"
    overlap_units: int = 1


class ExtractionSettings(BaseModel):
    field_batch_size: int = 30
    n_runs: int = 1
    number_locale: Literal["auto", "en", "it", "de"] = "auto"


class ProposalSettings(BaseModel):
    enabled: bool = True
    max_per_document: int = 10


class VerificationSettings(BaseModel):
    fuzzy_min_ratio: float = 0.85
    page_window: int = 1


class Settings(BaseModel):
    parser: str = "pdfplumber"
    llm: LLMSettings = LLMSettings()
    chunking: ChunkingSettings = ChunkingSettings()
    extraction: ExtractionSettings = ExtractionSettings()
    proposals: ProposalSettings = ProposalSettings()
    verification: VerificationSettings = VerificationSettings()


class Config(BaseModel):
    schema_version: Literal[1] = 1
    units: list[str] = []
    fields: list[FieldDef]
    settings: Settings = Settings()


def load_config(path: str | Path) -> Config:
    """Load and validate a YAML config, before any LLM call."""
    raise NotImplementedError
