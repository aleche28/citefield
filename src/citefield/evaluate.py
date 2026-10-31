"""Evaluation against the golden set built from reviewed values."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field

from citefield.config import Config, FieldDef
from citefield.output import (
    ExtractionResult,
    FieldResult,
    ScalarValue,
    TokenUsage,
    Value,
    normalize_text,
    value_key,
)

if TYPE_CHECKING:
    from citefield.extraction import Extractor

# Signal ranges for accuracy by signal: [low, high), the last one closed.
SIGNAL_RANGES = ((0.0, 0.5), (0.5, 0.85), (0.85, 1.0))
SCORED_SIGNALS = ("evidence_match", "model_confidence")


class FieldScore(BaseModel):
    """Counts for one field, summed over the documents where it was reviewed."""

    name: str
    documents: int = 0  # documents where the field was reviewed
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    unjudged: int = 0  # false positives the reviewer never saw: candidates for the golden set
    context_mismatches: int = 0  # true positives whose context differs from the golden one
    confirmed_absent: int = 0
    not_found_correct: int = 0  # of the confirmed-absent fields, predicted with no values
    errors: int = 0  # predicted field status "error"

    @computed_field
    @property
    def precision(self) -> float | None:
        return _ratio(self.true_positives, self.true_positives + self.false_positives)

    @computed_field
    @property
    def recall(self) -> float | None:
        return _ratio(self.true_positives, self.true_positives + self.false_negatives)

    @computed_field
    @property
    def not_found_accuracy(self) -> float | None:
        return _ratio(self.not_found_correct, self.confirmed_absent)

    def add(self, other: FieldScore) -> None:
        for name in type(self).model_fields:
            if name != "name":
                setattr(self, name, getattr(self, name) + getattr(other, name))


class SignalBucket(BaseModel):
    """Share of predicted values in a signal range that the golden set holds as correct."""

    signal: str
    low: float | None  # None for values where the signal is null
    high: float | None
    values: int = 0
    correct: int = 0

    @computed_field
    @property
    def precision(self) -> float | None:
        return _ratio(self.correct, self.values)


class UnjudgedValue(BaseModel):
    document_id: str
    field: str
    value_id: str
    raw_value: str
    context: str | None = None


class PredictionInfo(BaseModel):
    document_id: str
    run_id: str
    model: str
    prompt_version: str
    settings_hash: str
    tokens: TokenUsage


class EvalReport(BaseModel):
    golden: str | None = None  # folder of the golden outputs
    predictions: list[PredictionInfo]
    fields: list[FieldScore]
    total: FieldScore
    signals: list[SignalBucket]
    unjudged: list[UnjudgedValue] = []
    warnings: list[str] = []

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")


class EvalError(Exception):
    """The golden set or the predictions can't be loaded or paired."""


def evaluate(
    outputs: str | Path,
    config: Config,
    *,
    predictions: str | Path | None = None,
    documents: str | Path | None = None,
    extractor: Extractor | None = None,
) -> EvalReport:
    """Score extraction against the reviewed outputs in `outputs`.

    By default each golden document is extracted again with `config` (or `extractor`). The
    document is found at its recorded path, or by SHA-256 in `documents`. With `predictions`,
    the outputs already in that folder are scored instead, and nothing is extracted.
    """
    golden = _load_outputs(outputs)
    if not golden:
        raise EvalError(f"{outputs}: no output files")
    if predictions is not None:
        by_id = {p.document.document_id: p for p in _load_outputs(predictions)}
        pairs = []
        for g in golden:
            p = by_id.get(g.document.document_id)
            if p is None:
                raise EvalError(f"{predictions}: no output for {g.document.document_id}")
            if p.document.sha256 != g.document.sha256:
                raise EvalError(
                    f"{predictions}: {g.document.document_id} was extracted from a different "
                    "file than the golden output"
                )
            pairs.append((g, p))
    else:
        if extractor is None:
            from citefield.extraction import Extractor

            extractor = Extractor(config)
        by_hash = _hash_files(Path(documents)) if documents is not None else {}
        pairs = []
        for g in golden:
            path = _locate(g, by_hash, documents)
            pairs.append((g, extractor.extract(path, document_id=g.document.document_id)))
    return score(pairs, config).model_copy(update={"golden": str(outputs)})


def score(pairs: Iterable[tuple[ExtractionResult, ExtractionResult]], config: Config) -> EvalReport:
    """Score each prediction against its golden (reviewed) output.

    Only fields in `config` that were reviewed count: a field is reviewed when it has no
    pending values and has at least one reviewed value or is confirmed absent.
    """
    pairs = sorted(pairs, key=lambda pair: pair[0].run.started_at)
    scores = {f.name: FieldScore(name=f.name) for f in config.fields}
    buckets = {
        signal: [SignalBucket(signal=signal, low=lo, high=hi) for lo, hi in SIGNAL_RANGES]
        + [SignalBucket(signal=signal, low=None, high=None)]
        for signal in SCORED_SIGNALS
    }
    unjudged: list[UnjudgedValue] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()  # (document_id, value_id) of positives already counted

    for golden, predicted in pairs:
        doc_id = golden.document.document_id
        if golden.run.schema_hash != config.schema_hash():
            warnings.append(f"{doc_id}: golden output was made with a different field config")
        golden_names = {f.name for f in golden.fields}
        for name in sorted(golden_names - scores.keys()):
            warnings.append(f"{doc_id}: field {name!r} is not in the config; skipped")
        for fdef in config.fields:
            if fdef.name not in golden_names:
                warnings.append(f"{doc_id}: field {fdef.name!r} is not in the golden output")
                continue
            g_field = golden.field(fdef.name)
            if not _reviewed(g_field):
                continue
            try:
                p_field = predicted.field(fdef.name)
            except KeyError:
                p_field = FieldResult(name=fdef.name, status="error", error="not extracted")
            truth = _truth(doc_id, fdef, g_field, seen)
            scores[fdef.name].add(_score_field(doc_id, fdef, truth, p_field, buckets, unjudged))

    total = FieldScore(name="all")
    for s in scores.values():
        total.add(s)
    return EvalReport(
        predictions=[
            PredictionInfo(
                document_id=p.document.document_id,
                run_id=p.run.run_id,
                model=p.run.model,
                prompt_version=p.run.prompt_version,
                settings_hash=p.run.settings_hash,
                tokens=p.run.tokens,
            )
            for _, p in pairs
        ],
        fields=list(scores.values()),
        total=total,
        signals=[b for signal in SCORED_SIGNALS for b in buckets[signal]],
        unjudged=unjudged,
        warnings=warnings,
    )


@dataclass
class _Truth:
    """The reviewed values of one field in one golden output, by value key."""

    positives: dict[ScalarValue, set[str]] = field(default_factory=dict)  # key -> contexts
    negatives: set[ScalarValue] = field(default_factory=set)
    excluded: set[ScalarValue] = field(default_factory=set)
    confirmed_absent: bool = False


def _reviewed(f: FieldResult) -> bool:
    statuses = [v.review.status for v in f.values]
    if "pending" in statuses:
        return False
    return bool(statuses) or f.review.status == "confirmed_absent"


def _truth(doc_id: str, fdef: FieldDef, g_field: FieldResult, seen: set[tuple[str, str]]) -> _Truth:
    truth = _Truth(confirmed_absent=g_field.review.status == "confirmed_absent")
    # Values in the prompt's examples measure copying, not extraction.
    truth.excluded = {value_key(e, e) for e in fdef.examples}
    for v in g_field.values:
        review = v.review
        if review.status in ("accepted", "added", "edited"):
            if review.carried_from and (doc_id, v.value_id) in seen:
                truth.excluded.add(_golden_key(v))  # carried over: counted once already
                continue
            seen.add((doc_id, v.value_id))
            truth.positives.setdefault(_golden_key(v), set()).add(_context(v))
        if review.status in ("edited", "rejected"):
            truth.negatives.add(value_key(v.value, v.raw_value))
    truth.negatives -= truth.positives.keys()
    return truth


def _score_field(
    doc_id: str,
    fdef: FieldDef,
    truth: _Truth,
    p_field: FieldResult,
    buckets: dict[str, list[SignalBucket]],
    unjudged: list[UnjudgedValue],
) -> FieldScore:
    s = FieldScore(name=fdef.name, documents=1)
    if p_field.status == "error":
        s.errors = 1
    predicted: dict[ScalarValue, list[Value]] = {}
    for v in p_field.values:
        key = value_key(v.value, v.raw_value)
        if key not in truth.excluded:
            predicted.setdefault(key, []).append(v)

    for key, values in predicted.items():
        correct = key in truth.positives
        if correct:
            s.true_positives += 1
            if {_context(v) for v in values} != truth.positives[key]:
                s.context_mismatches += 1
        else:
            s.false_positives += 1
            if key not in truth.negatives:
                s.unjudged += 1
                unjudged.extend(
                    UnjudgedValue(
                        document_id=doc_id,
                        field=fdef.name,
                        value_id=v.value_id,
                        raw_value=v.raw_value,
                        context=v.context,
                    )
                    for v in values
                )
        for v in values:
            for signal, signal_buckets in buckets.items():
                bucket = _bucket(signal_buckets, getattr(v.signals, signal))
                bucket.values += 1
                bucket.correct += correct
    s.false_negatives = len(truth.positives.keys() - predicted.keys())
    if truth.confirmed_absent:
        s.confirmed_absent = 1
        s.not_found_correct = int(p_field.status == "not_found")
    return s


def _bucket(buckets: list[SignalBucket], x: float | None) -> SignalBucket:
    if x is None:
        return buckets[-1]
    for b in buckets[:-2]:
        if x < b.high:
            return b
    return buckets[-2]


def _golden_key(v: Value) -> ScalarValue:
    if v.review.status == "edited":
        return value_key(v.review.reviewed_value, v.raw_value)
    return value_key(v.value, v.raw_value)


def _context(v: Value) -> str:
    return normalize_text(v.context) if v.context else ""


def _ratio(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def _load_outputs(folder: str | Path) -> list[ExtractionResult]:
    folder = Path(folder)
    if not folder.is_dir():
        raise EvalError(f"{folder}: not a directory")
    return [ExtractionResult.from_json(p) for p in sorted(folder.glob("*.json"))]


def _hash_files(folder: Path) -> dict[str, Path]:
    if not folder.is_dir():
        raise EvalError(f"{folder}: not a directory")
    return {_sha256(path): path for path in sorted(folder.iterdir()) if path.is_file()}


def _sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _locate(
    golden: ExtractionResult, by_hash: dict[str, Path], documents: str | Path | None
) -> Path:
    doc = golden.document
    if documents is not None:
        path = by_hash.get(doc.sha256)
        if path is None:
            raise EvalError(f"{documents}: no file matches {doc.document_id} (sha256)")
        return path
    path = Path(doc.path)
    if not path.is_file():
        raise EvalError(f"{doc.path}: not found; pass the folder that holds it as documents")
    if _sha256(path) != doc.sha256:
        raise EvalError(f"{doc.path}: not the file the golden output was made from")
    return path
