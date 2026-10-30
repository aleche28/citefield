"""Evidence matching, number parsing and unit conversion."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from difflib import SequenceMatcher

_QUOTES = str.maketrans({"‘": "'", "’": "'", "‚": "'", "‛": "'", "“": '"', "”": '"', "„": '"'})
# Hyphens and dashes are dropped entirely: PDFs break words at line ends ("pro-\ncedure"),
# and the model may or may not keep the hyphen of a code like "MEP-803A".
_DASHES_AND_SPACE = re.compile(r"[\s\-‐‑‒–—―­]+")
# Matching blocks shorter than this aren't worth aligning a window on.
_MIN_ANCHOR = 3


def normalize_for_match(text: str) -> str:
    """Fold ligatures, case, quotes, dashes, hyphenation and whitespace.

    Whitespace is removed rather than collapsed, because some PDFs lose the spaces between
    words ("Permissionisgranted") and others add spaces inside them.
    """
    text = unicodedata.normalize("NFKC", text).casefold().translate(_QUOTES)
    return _DASHES_AND_SPACE.sub("", text)


def partial_ratio(needle: str, haystack: str) -> float:
    """Best similarity (0-1) between `needle` and any same-length window of `haystack`."""
    if not needle:
        return 0.0
    if needle in haystack:
        return 1.0
    if len(haystack) <= len(needle):
        return SequenceMatcher(None, needle, haystack, autojunk=False).ratio()
    best = 0.0
    blocks = SequenceMatcher(None, haystack, needle, autojunk=False).get_matching_blocks()
    starts = {max(0, block.a - block.b) for block in blocks if block.size >= _MIN_ANCHOR}
    for start in starts:
        window = haystack[start : start + len(needle)]
        best = max(best, SequenceMatcher(None, needle, window, autojunk=False).ratio())
        if best == 1.0:
            break
    return best


def evidence_match(
    quote: str,
    page: int,
    pages: Mapping[int, str],
    *,
    page_window: int = 1,
) -> float:
    """Best match (0-1) of `quote` on `page` ± `page_window`; 0 when nothing matched.

    `pages` maps 1-based page numbers to their text.
    """
    needle = normalize_for_match(quote)
    best = 0.0
    for number in range(page - page_window, page + page_window + 1):
        text = pages.get(number)
        if text is None:
            continue
        best = max(best, partial_ratio(needle, normalize_for_match(text)))
        if best == 1.0:
            break
    return round(best, 4)
