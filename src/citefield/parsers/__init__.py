"""Document parsers. Third-party parsers register through the `citefield.parsers` entry point."""

from __future__ import annotations

from importlib.metadata import entry_points

from citefield.parsers.base import DocumentParser, Locator, ParsedDocument, ParserInfo, Table, Unit

__all__ = [
    "DocumentParser",
    "Locator",
    "ParsedDocument",
    "ParserInfo",
    "Table",
    "Unit",
    "available_parsers",
    "get_parser",
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
