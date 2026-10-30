"""Command-line interface: a thin layer over the library."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from citefield import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="citefield", description=__doc__)
    parser.add_argument("--version", action="version", version=f"citefield {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="extract fields; one JSON per document")
    extract.add_argument("path", help="file or directory")
    extract.add_argument("-c", "--config", required=True)
    extract.add_argument("-o", "--output", required=True)
    extract.add_argument("--dry-run", action="store_true", help="print the plan, no LLM calls")
    extract.add_argument("--workers", type=int, default=1)

    reextract = sub.add_parser("reextract", help="re-run and carry reviews over")
    reextract.add_argument("path")
    reextract.add_argument("--previous", required=True)

    inspect = sub.add_parser("inspect", help="show parsed text, tables and low-text units")
    inspect.add_argument("path")
    inspect.add_argument("--parser")

    validate = sub.add_parser("validate-config", help="check the schema and units")
    validate.add_argument("config")

    proposals = sub.add_parser("proposals", help="work with proposed fields")
    proposals_sub = proposals.add_subparsers(dest="proposals_command", required=True)
    report = proposals_sub.add_parser("report", help="count recurring proposals across outputs")
    report.add_argument("outputs")

    evaluate = sub.add_parser("eval", help="evaluate against the golden set")
    evaluate.add_argument("outputs")
    evaluate.add_argument("-c", "--config", required=True)
    evaluate.add_argument("--parser")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = {
        "validate-config": _validate_config,
        "inspect": _inspect,
        "extract": _extract,
    }
    command = commands.get(args.command)
    if command is None:
        print(f"citefield {args.command}: not implemented yet", file=sys.stderr)
        return 2
    return command(args)


def _error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def _load_config(path: str):
    from citefield.config import load_config

    try:
        return load_config(path)
    except OSError as exc:
        raise _CliError(f"can't read config: {exc}") from exc
    except yaml.YAMLError as exc:
        raise _CliError(f"{path}: invalid YAML: {exc}") from exc
    except ValidationError as exc:
        raise _CliError(f"{path}: invalid config\n{exc}") from exc


class _CliError(Exception):
    pass


def _validate_config(args: argparse.Namespace) -> int:
    try:
        config = _load_config(args.config)
    except _CliError as exc:
        return _error(str(exc))
    print(f"{args.config}: OK, {len(config.fields)} fields")
    return 0


def _inspect(args: argparse.Namespace) -> int:
    from citefield.parsers import get_parser

    path = Path(args.path)
    try:
        parser = get_parser(args.parser or "pdfplumber")
    except ValueError as exc:
        return _error(str(exc))
    if not path.is_file():
        return _error(f"{path}: no such file")
    if not parser.supports(path):
        return _error(f"{path}: not supported by the {parser.name} parser")
    document = parser.parse(path)
    for unit in document.units:
        label = f"page {unit.locator.page}" if unit.locator.page else unit.id
        flag = " · low text" if unit.low_text else ""
        print(f"[[{label}{flag}]]")
        print(unit.text.rstrip())
        print()
    low = [u.locator.page or u.id for u in document.units if u.low_text]
    print(
        f"--- {path.name}: {len(document.units)} units, parser {document.parser.name} "
        f"{document.parser.version}, {len(low)} low-text: {low}"
    )
    return 0


def _extract(args: argparse.Namespace) -> int:
    from citefield.extraction import ExtractionError, Extractor
    from citefield.planning import DocumentTooLarge

    try:
        config = _load_config(args.config)
    except _CliError as exc:
        return _error(str(exc))
    extractor = Extractor(config)
    root = Path(args.path)
    if root.is_dir():
        files = sorted(p for p in root.iterdir() if p.is_file() and extractor.parser.supports(p))
    elif root.is_file():
        files = [root]
    else:
        return _error(f"{root}: no such file or directory")
    if not files:
        return _error(f"{root}: no supported documents")

    out = Path(args.output)
    failures = 0
    for path in files:
        try:
            if args.dry_run:
                plan = extractor.plan(extractor.parse(path))
                print(
                    f"{path}: {plan.chunks} chunk(s) × {len(plan.batches)} field batch(es) × "
                    f"{plan.n_runs} run(s) = {plan.calls} call(s); document "
                    f"{plan.document_tokens} tokens, largest prompt {plan.max_prompt_tokens} "
                    f"of {plan.input_budget} budget"
                )
                continue
            result = extractor.extract(path)
        except (ExtractionError, DocumentTooLarge) as exc:
            failures += 1
            print(f"error: {exc}", file=sys.stderr)
            continue
        out.mkdir(parents=True, exist_ok=True)
        target = out / f"{result.document.document_id}.json"
        result.to_json(target)
        counts: dict[str, int] = {}
        for field in result.fields:
            counts[field.status] = counts.get(field.status, 0) + 1
        summary = ", ".join(f"{n} {status}" for status, n in sorted(counts.items()))
        print(
            f"{path} -> {target}: {summary}; {result.run.llm_calls} call(s), "
            f"{result.run.tokens.input}+{result.run.tokens.output} tokens"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
