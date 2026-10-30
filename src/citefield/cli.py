"""Command-line interface: a thin layer over the library."""

from __future__ import annotations

import argparse
import sys

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
    print(f"citefield {args.command}: not implemented yet", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
