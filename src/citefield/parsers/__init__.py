"""Document parsers. Third-party parsers register through the `citefield.parsers` entry point."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

from citefield.parsers.base import DocumentParser, Locator, ParsedDocument, ParserInfo, Table, Unit

__all__ = [
    "DocumentParser",
    "Locator",
    "ParseError",
    "ParsedDocument",
    "ParserInfo",
    "Table",
    "Unit",
    "available_parsers",
    "get_parser",
    "parse_document",
]

ENTRY_POINT_GROUP = "citefield.parsers"


def available_parsers() -> list[str]:
    return sorted(ep.name for ep in entry_points(group=ENTRY_POINT_GROUP))


def get_parser(name: str) -> DocumentParser:
    """Instantiate the parser registered under `name`."""
    matches = entry_points(group=ENTRY_POINT_GROUP, name=name)
    if not matches:
        known = ", ".join(available_parsers()) or "none"
        raise ValueError(f"unknown parser {name!r} (available: {known})")
    return next(iter(matches)).load()()


class ParseError(Exception):
    """A document can't be parsed: unsupported format, or an unreadable or broken file."""


def parse_document(path: str | Path, parser: DocumentParser) -> ParsedDocument:
    """Parse `path` with `parser`, turning any failure into a `ParseError`."""
    path = Path(path)
    if not parser.supports(path):
        raise ParseError(f"{path}: not supported by the {parser.name} parser")
    try:
        return parser.parse(path)
    except Exception as exc:
        raise ParseError(f"{path}: can't parse: {type(exc).__name__}: {exc}") from exc
