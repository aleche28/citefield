import pytest

from citefield.verify import evidence_match, normalize_for_match, partial_ratio


@pytest.mark.parametrize(
    "a, b",
    [
        ("Permission is granted", "Permissionisgranted"),
        ("pro-\ncedure", "procedure"),
        ("MEP-803A", "MEP803A"),
        ("ﬁlter", "filter"),
        ("“Output”", '"output"'),
        ("Engine  Manufacturer", "engine manufacturer"),
        ("10 kW – 60 Hz", "10 kW - 60 Hz"),
    ],
)
def test_normalize_for_match(a, b):
    assert normalize_for_match(a) == normalize_for_match(b)


def test_partial_ratio():
    assert partial_ratio("onan", "manufactureronanmodel") == 1.0
    assert partial_ratio("", "anything") == 0.0
    assert 0.85 < partial_ratio("manufacturer0nan", "enginemanufactureronanmodel") < 1.0


PAGES = {
    1: "Cover page",
    2: "Table 1. Leading Particulars.\nManufacturer Onan\nModel DN4M",
    3: "Cooling System:\nType Pressurized radiator and pump",
    5: "Firing Order 1, 3, 4, 2",
}


@pytest.mark.parametrize(
    "quote, page",
    [
        ("Manufacturer Onan", 2),
        ("manufacturer  onan", 2),  # case and whitespace
        ("Type Pressurized radiator and pump", 2),  # on the next page, within the window
    ],
)
def test_evidence_match_exact(quote, page):
    assert evidence_match(quote, page, PAGES, page_window=1) == 1.0


@pytest.mark.parametrize(
    "quote, page, low, high",
    [
        ("Manufacturer 0nan", 2, 0.85, 1.0),  # a near match keeps its score
        ("Manufacturer Cummins", 2, 0.4, 0.85),  # a partial match is reported, not zeroed
        ("Firing Order 1, 3, 4, 2", 2, 0.0, 0.85),  # three pages away
    ],
)
def test_evidence_match_reports_the_raw_best_score(quote, page, low, high):
    assert low <= evidence_match(quote, page, PAGES, page_window=1) < high


def test_evidence_match_is_zero_when_nothing_matched():
    assert evidence_match("Manufacturer Onan", 99, PAGES) == 0.0  # page doesn't exist
    assert evidence_match("zzzzqqqq", 2, PAGES) == 0.0


def test_evidence_match_window_zero_checks_only_the_cited_page():
    assert evidence_match("Type Pressurized radiator", 2, PAGES, page_window=0) < 0.85
