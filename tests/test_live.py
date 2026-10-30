"""End-to-end runs against a real LLM. Opt in with `uv run pytest -m live`; never run in CI."""

import os
from pathlib import Path

import pytest

from citefield import Extractor, load_config

ROOT = Path(__file__).resolve().parent.parent

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY unset"),
]


def test_generator_manual():
    config = load_config(ROOT / "examples" / "generator.yaml")
    result = Extractor(config).extract(ROOT / "corpus" / "manuals" / "tm-9-6115-642-10.pdf")

    engine = result.field("engine_manufacturer")
    assert engine.status == "found"
    assert any(v.value.casefold() == "onan" for v in engine.values)
    assert all(v.signals.evidence_match >= 0.85 for v in engine.values)
    assert result.field("machine_category").values[0].value == "generator"
    assert result.field("refrigerant_type").status == "not_found"
