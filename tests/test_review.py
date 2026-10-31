import sys
from pathlib import Path

import pytest
from fakes import output, value
from pdfgen import write_pdf

from citefield.output import DocumentInfo, ExtractionResult, make_value_id
from citefield.parsers import parse_document
from citefield.parsers.pdfplumber import PdfplumberParser
from citefield.review import apply_review, load_decisions


def generator_output():
    return output(
        "tm",
        engine_manufacturer=[value("engine_manufacturer", "Onan")],
        model_designation=[
            value("model_designation", "MEP-803A", context="60 Hz"),
            value("model_designation", "MEP-813", context="400 Hz"),
        ],
        refrigerant_type=[value("refrigerant_type", "R-134a")],
    )


def vid(field, raw, context=None):
    return make_value_id(field, raw, raw, context)


def test_apply_review_writes_decisions(tmp_path):
    path = tmp_path / "tm.json"
    generator_output().to_json(path)
    decisions = {
        "reviewer": "alessio",
        "fields": {
            "engine_manufacturer": {
                "values": [{"value_id": vid("engine_manufacturer", "Onan"), "status": "accepted"}]
            },
            "model_designation": {
                "values": [
                    {
                        "value_id": vid("model_designation", "MEP-803A", "60 Hz"),
                        "status": "accepted",
                    },
                    {
                        "value_id": vid("model_designation", "MEP-813", "400 Hz"),
                        "status": "edited",
                        "reviewed_value": "MEP-813A",
                    },
                ],
                "added": [
                    {
                        "raw_value": "MEP-803A",
                        "context": "50 Hz",
                        "evidence": [{"page": 2, "quote": "MEP-803A (50/60 Hz)"}],
                    }
                ],
            },
            "refrigerant_type": {
                "status": "confirmed_absent",
                "values": [{"value_id": vid("refrigerant_type", "R-134a"), "status": "rejected"}],
            },
        },
    }

    result = apply_review(path, decisions)

    engine = result.field("engine_manufacturer").values[0].review
    assert (engine.status, engine.reviewer) == ("accepted", "alessio")
    assert engine.reviewed_at is not None
    models = result.field("model_designation").values
    assert [v.review.status for v in models] == ["accepted", "edited", "added"]
    assert models[1].review.reviewed_value == "MEP-813A"
    added = models[2]
    assert added.value_id == vid("model_designation", "MEP-803A", "50 Hz")
    assert added.value == "MEP-803A"
    assert added.signals.citation_count == 1
    refrigerant = result.field("refrigerant_type")
    assert refrigerant.review.status == "confirmed_absent"
    assert refrigerant.values[0].review.status == "rejected"
    # the input is left as it was
    assert generator_output().model_dump() == type(result).from_json(path).model_dump()


def test_apply_review_does_not_change_its_input():
    original = generator_output()
    decision = {"values": [{"value_id": vid("engine_manufacturer", "Onan"), "status": "accepted"}]}
    apply_review(original, {"fields": {"engine_manufacturer": decision}})
    assert original.field("engine_manufacturer").values[0].review.status == "pending"


def test_added_value_updates_field_status_and_applies_again():
    decisions = {
        "fields": {
            "engine_model": {
                "added": [{"raw_value": "DN4M", "evidence": [{"page": 3, "quote": "DN4M"}]}]
            }
        }
    }
    result = apply_review(output("tm", engine_model="not_found"), decisions)
    assert result.field("engine_model").status == "found"
    again = apply_review(result, decisions)
    assert [v.raw_value for v in again.field("engine_model").values] == ["DN4M"]


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"firing_order": {"status": "confirmed_absent"}}, "not in the output"),
        (
            {"engine_manufacturer": {"values": [{"value_id": "nope", "status": "accepted"}]}},
            "no value with id nope",
        ),
        ({"engine_manufacturer": {"status": "confirmed_absent"}}, "not rejected"),
        (
            {
                "engine_manufacturer": {
                    "added": [{"raw_value": "onan", "evidence": [{"page": 1, "quote": "Onan"}]}]
                }
            },
            "already in the output",
        ),
    ],
)
def test_apply_review_rejects_bad_decisions(fields, message):
    with pytest.raises(ValueError, match=message):
        apply_review(generator_output(), {"fields": fields})


@pytest.mark.parametrize(
    "decision",
    [
        {"value_id": "x", "status": "edited"},
        {"value_id": "x", "status": "accepted", "reviewed_value": "y"},
    ],
)
def test_reviewed_value_goes_with_edited(decision):
    with pytest.raises(ValueError, match="reviewed_value"):
        apply_review(
            generator_output(), {"fields": {"engine_manufacturer": {"values": [decision]}}}
        )


def test_also_accept_is_stored_as_equivalents():
    mid = vid("engine_manufacturer", "Onan")
    added = {
        "raw_value": "Kubota",
        "also_accept": ["Kubota Corp"],
        "evidence": [{"page": 1, "quote": "Kubota"}],
    }
    decisions = {
        "fields": {
            "engine_manufacturer": {
                "values": [{"value_id": mid, "status": "accepted", "also_accept": ["Onan Corp"]}],
                "added": [added],
            }
        }
    }
    values = apply_review(generator_output(), decisions).field("engine_manufacturer").values
    assert [v.review.equivalents for v in values] == [["Onan Corp"], ["Kubota Corp"]]


def test_also_accept_needs_a_positive_status():
    decision = {"value_id": "x", "status": "rejected", "also_accept": ["y"]}
    with pytest.raises(ValueError, match="also_accept"):
        apply_review(
            generator_output(), {"fields": {"engine_manufacturer": {"values": [decision]}}}
        )


def test_added_value_needs_evidence():
    with pytest.raises(ValueError, match="needs evidence"):
        apply_review(
            generator_output(),
            {"fields": {"engine_model": {"added": [{"raw_value": "DN4M", "evidence": []}]}}},
        )


def test_load_decisions(tmp_path):
    path = tmp_path / "tm.review.yaml"
    path.write_text(
        "reviewer: alessio\nfields:\n  refrigerant_type:\n    status: confirmed_absent\n",
        encoding="utf-8",
    )
    decisions = load_decisions(path)
    assert decisions.fields["refrigerant_type"].status == "confirmed_absent"


def test_review_script_template_round_trips(tmp_path, capsys):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from review import main, template

    manual = write_pdf(tmp_path / "tm.pdf", ["Onan MEP-803A", "Engine model DN4M"])
    result = apply_review(
        generator_output(),
        {
            "fields": {
                "model_designation": {
                    "values": [
                        {
                            "value_id": vid("model_designation", "MEP-813", "400 Hz"),
                            "status": "edited",
                            "reviewed_value": "MEP-813A",
                            "also_accept": ["MEP 813 A"],
                        }
                    ]
                }
            }
        },
    )
    parsed = parse_document(manual, PdfplumberParser())
    result.document = DocumentInfo(
        document_id="tm", path=parsed.path, sha256=parsed.sha256, units=2, parser=parsed.parser
    )
    source, decisions, reviewed = (tmp_path / n for n in ("o.json", "d.yaml", "r.json"))
    result.to_json(source)
    text = template(result)
    assert '#   p.1: "MEP-803A"' in text
    assert 'also_accept: ["MEP 813 A"]' in text
    text = text.replace("        status: pending", "        status: accepted")
    added = """added:
      - {raw_value: DN4M, evidence: [{page: 2, quote: "Engine model DN4M"}]}
      - {raw_value: DN4X, evidence: [{page: 2, quote: "Engine type DN4X"}]}"""
    text = text.replace("added: []", added, 1)
    decisions.write_text(text, encoding="utf-8")

    assert main(["apply", str(source), str(decisions), "-o", str(reviewed)]) == 0
    values = {v.raw_value: v for f in ExtractionResult.from_json(reviewed).fields for v in f.values}
    assert {k: v.review.status for k, v in values.items()} == {
        "Onan": "accepted",
        "DN4M": "added",
        "DN4X": "added",
        "MEP-803A": "accepted",
        "MEP-813": "edited",
        "R-134a": "accepted",
    }
    assert values["MEP-813"].review.equivalents == ["MEP 813 A"]
    assert values["DN4M"].signals.evidence_match == 1.0
    assert values["DN4X"].signals.evidence_match < 0.85
    assert "'DN4X' has evidence_match" in capsys.readouterr().err


def test_added_value_evidence_is_verified_against_pages():
    added = {"raw_value": "DN4M", "evidence": [{"page": 3, "quote": "Model DN4M"}]}
    decisions = {"fields": {"engine_model": {"added": [added]}}}
    unverified = apply_review(output(engine_model="not_found"), decisions)
    verified = apply_review(output(engine_model="not_found"), decisions, pages={2: "Model DN4M"})
    assert unverified.field("engine_model").values[0].signals.evidence_match == 0.0
    assert verified.field("engine_model").values[0].signals.evidence_match == 1.0
