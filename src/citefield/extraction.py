"""LLM calls, response validation and retries."""

from __future__ import annotations

import uuid
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from pydantic import ValidationError

from citefield.config import Config, FieldDef, Settings
from citefield.llm.base import LLMBackend
from citefield.merge import Draft, field_status, merge
from citefield.output import (
    DocumentInfo,
    ExtractionResult,
    FieldResult,
    OutputWarning,
    QuoteEvidence,
    RunInfo,
    TokenUsage,
)
from citefield.parsers import get_parser
from citefield.parsers.base import DocumentParser, ParsedDocument
from citefield.planning import Plan, make_plan
from citefield.prompts import extract_v1
from citefield.verify import evidence_match

# Field types whose values are parsed in code; the others are not implemented yet and keep
# value null.
SUPPORTED_TYPES = {"string", "enum"}


class ExtractionError(Exception):
    """Extraction can't start: missing settings, unsupported options, unreadable file."""


class Extractor:
    """Runs extraction with the parser and LLM backend named in the config's settings."""

    def __init__(
        self,
        config: Config,
        *,
        parser: DocumentParser | None = None,
        backend: LLMBackend | None = None,
    ) -> None:
        self.config = config
        self._parser = parser
        self._backend = backend

    @property
    def parser(self) -> DocumentParser:
        if self._parser is None:
            self._parser = get_parser(self.config.settings.parser)
        return self._parser

    @property
    def backend(self) -> LLMBackend:
        if self._backend is None:
            from citefield.llm.litellm import LiteLLMBackend

            llm = self.config.settings.llm
            if not llm.model:
                raise ExtractionError("settings.llm.model is not set")
            self._backend = LiteLLMBackend(llm.model, llm.temperature, llm.max_retries)
        return self._backend

    def parse(self, path: str | Path) -> ParsedDocument:
        path = Path(path)
        if not self.parser.supports(path):
            raise ExtractionError(f"{path}: not supported by the {self.parser.name} parser")
        try:
            return self.parser.parse(path)
        except Exception as exc:
            raise ExtractionError(f"{path}: can't parse: {type(exc).__name__}: {exc}") from exc

    def plan(self, document: ParsedDocument) -> Plan:
        settings = self.config.settings
        if settings.extraction.n_runs != 1:
            raise ExtractionError("n_runs > 1 is not supported yet")
        return make_plan(
            document,
            self.config.fields,
            self.backend,
            chunking=settings.chunking,
            batch_size=settings.extraction.field_batch_size,
        )

    def extract(self, path: str | Path, *, document_id: str | None = None) -> ExtractionResult:
        started_at = datetime.now().astimezone()
        document = self.parse(path)
        plan = self.plan(document)
        settings = self.config.settings
        pages = {u.locator.page: u.text for u in document.units if u.locator.page is not None}
        text = extract_v1.render_units(document.units)
        warnings = _document_warnings(document, self.config.fields)

        tokens = TokenUsage()
        calls = 0
        drafts: dict[str, list[Draft]] = {f.name: [] for f in self.config.fields}
        errors: dict[str, str] = {}
        for batch in plan.batches:
            messages = extract_v1.build_messages(batch, text)
            response, attempts, error = None, 0, None
            for _ in range(settings.llm.max_retries + 1):
                attempts += 1
                try:
                    completion = self.backend.complete_structured(
                        messages, extract_v1.ExtractResponse
                    )
                except ValidationError as exc:
                    error = f"invalid response after {attempts} attempt(s): {exc}"
                    continue
                except Exception as exc:  # API errors; the backend already retried them
                    error = f"{type(exc).__name__}: {exc}"
                    break
                tokens.input += completion.input_tokens or 0
                tokens.output += completion.output_tokens or 0
                response = completion.parsed
                break
            calls += attempts
            if response is None:
                for field in batch:
                    errors[field.name] = (error or "no response")[:1000]
                continue

            by_name = {f.name: f for f in batch}
            for answer in response.fields:
                field = by_name.get(answer.name)
                if field is None:
                    warnings.append(OutputWarning(code="unexpected_field", raw=answer.name))
                    continue
                for candidate in answer.candidates:
                    draft = _draft(field, candidate, pages, settings, warnings)
                    if draft is not None:
                        drafts[field.name].append(draft)

        fields = []
        for field in self.config.fields:
            if field.name in errors:
                fields.append(
                    FieldResult(name=field.name, status="error", error=errors[field.name])
                )
                continue
            values = merge(field.name, drafts[field.name])
            min_ratio = settings.verification.fuzzy_min_ratio
            for value in values:
                if value.signals.evidence_match < min_ratio:
                    warnings.append(
                        OutputWarning(
                            code="evidence_not_verified",
                            field=field.name,
                            raw=value.raw_value,
                            message=f"best evidence_match {value.signals.evidence_match} "
                            f"is below fuzzy_min_ratio {min_ratio}",
                        )
                    )
            fields.append(FieldResult(name=field.name, status=field_status(values), values=values))

        return ExtractionResult(
            citefield_version=version("citefield"),
            document=DocumentInfo(
                document_id=document_id or Path(document.path).stem,
                path=document.path,
                sha256=document.sha256,
                units=len(document.units),
                parser=document.parser,
            ),
            run=RunInfo(
                run_id=uuid.uuid4().hex,
                started_at=started_at,
                model=settings.llm.model or getattr(self.backend, "name", "unknown"),
                prompt_version=extract_v1.VERSION,
                schema_hash=self.config.schema_hash(),
                settings_hash=self.config.settings_hash(),
                n_runs=plan.n_runs,
                chunks=plan.chunks,
                llm_calls=calls,
                tokens=tokens,
            ),
            fields=fields,
            warnings=warnings,
        )

    def reextract(self, path: str | Path, previous: str | Path) -> ExtractionResult:
        """Re-run extraction and carry reviews over from a previous output."""
        raise NotImplementedError


def _document_warnings(document: ParsedDocument, fields: list[FieldDef]) -> list[OutputWarning]:
    warnings = []
    low = [u.locator.page for u in document.units if u.low_text and u.locator.page is not None]
    if low:
        warnings.append(OutputWarning(code="low_text_units", units=low))
    for field in fields:
        if field.type not in SUPPORTED_TYPES:
            warnings.append(
                OutputWarning(
                    code="unsupported_field_type",
                    field=field.name,
                    message=f"{field.type} values are not parsed yet; value stays null",
                )
            )
    return warnings


def _draft(
    field: FieldDef,
    candidate: extract_v1.Candidate,
    pages: dict[int, str],
    settings: Settings,
    warnings: list[OutputWarning],
) -> Draft | None:
    """Turn one LLM candidate into a verified draft, or None if it has no usable evidence."""
    raw_value = candidate.raw_value.strip()
    evidence = [
        QuoteEvidence(page=e.page, quote=e.quote.strip())
        for e in candidate.evidence
        if e.quote.strip()
    ]
    if not raw_value or not evidence:
        return None  # a candidate without evidence is not a value (ADR-0003)

    value = None
    if field.type == "string":
        value = raw_value
    elif field.type == "enum":
        allowed = {v.casefold(): v for v in field.values or []}
        value = allowed.get(raw_value.casefold())
        if value is None:
            warnings.append(
                OutputWarning(code="enum_value_unknown", field=field.name, raw=raw_value)
            )

    verification = settings.verification
    matches = [
        evidence_match(
            e.quote,
            e.page,
            pages,
            page_window=verification.page_window,
        )
        for e in evidence
    ]
    return Draft(
        raw_value=raw_value,
        raw_unit=(candidate.raw_unit or "").strip() or None,
        value=value,
        context=(candidate.context or "").strip() or None,
        evidence=evidence,
        matches=matches,
        model_confidence=min(max(candidate.model_confidence, 0.0), 1.0),
    )
