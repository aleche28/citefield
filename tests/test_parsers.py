import hashlib

import pytest
from pdfgen import write_pdf

from citefield.parsers import available_parsers, get_parser


def test_registry():
    assert {"pdfplumber", "markdown"} <= set(available_parsers())
    assert get_parser("pdfplumber").name == "pdfplumber"
    with pytest.raises(ValueError, match="unknown parser 'nope'"):
        get_parser("nope")


def test_pdfplumber_pages(tmp_path):
    long_text = "\n".join(
        f"Line {i}: the quick brown fox jumps over the lazy dog" for i in range(8)
    )
    path = write_pdf(tmp_path / "m.pdf", ["Engine manufacturer: Onan", long_text, ""])
    parser = get_parser("pdfplumber")
    assert parser.supports(path)
    document = parser.parse(path)
    assert document.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert document.parser.name == "pdfplumber"
    assert [u.locator.page for u in document.units] == [1, 2, 3]
    assert document.units[0].text == "Engine manufacturer: Onan"
    assert [u.low_text for u in document.units] == [True, False, True]
