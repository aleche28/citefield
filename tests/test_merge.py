from citefield.merge import Draft, field_status, merge
from citefield.output import QuoteEvidence


def draft(value, *pages, context=None, match=1.0, confidence=0.9):
    return Draft(
        raw_value=value,
        value=value,
        context=context,
        evidence=[QuoteEvidence(page=p, quote=f"{value} on {p}") for p in pages],
        matches=[match] * len(pages),
        model_confidence=confidence,
    )


def test_same_value_merges_evidence():
    values = merge("engine", [draft("Onan", 2), draft("onan", 5, confidence=0.7)])
    assert len(values) == 1
    (value,) = values
    assert value.raw_value == "Onan"
    assert [e.page for e in value.evidence] == [2, 5]
    assert value.signals.citation_count == 2
    assert value.signals.model_confidence == 0.9
    assert value.review.status == "pending"


def test_value_id_is_stable_and_normalized():
    a = merge("engine", [draft("Onan  Corp", 2)])[0]
    b = merge("engine", [draft("onan corp", 9)])[0]
    c = merge("engine", [draft("Onan Corp", 2, context="60 Hz")])[0]
    assert a.value_id == b.value_id
    assert a.value_id != c.value_id


def test_evidence_match_is_best_of_evidence():
    d = draft("Onan", 2, 3)
    d.matches = [0.0, 0.92]
    assert merge("engine", [d])[0].signals.evidence_match == 0.92


def test_field_status():
    assert field_status([]) == "not_found"
    assert field_status(merge("m", [draft("A", 1)])) == "found"
    different_contexts = merge(
        "m", [draft("A", 1, context="60 Hz"), draft("B", 1, context="400 Hz")]
    )
    assert field_status(different_contexts) == "found"
    same_context = merge("m", [draft("A", 1, context="60 Hz"), draft("B", 1, context="60 hz")])
    assert field_status(same_context) == "conflict"
    missing_context = merge("m", [draft("A", 1, context="60 Hz"), draft("B", 1)])
    assert field_status(missing_context) == "conflict"
    same_value_two_contexts = merge("m", [draft("A", 1, context="x"), draft("A", 1)])
    assert field_status(same_value_two_contexts) == "found"
