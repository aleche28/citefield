from pathlib import Path

import pytest
from pydantic import ValidationError

from citefield.config import Config, load_config
from citefield.output import ExtractionResult

ROOT = Path(__file__).resolve().parent.parent


def make(fields, **extra):
    return Config(fields=fields, **extra)


def test_load_config_from_yaml(tmp_path):
    path = tmp_path / "fields.yaml"
    path.write_text(
        """
units:
  - "bottle = [count]"
  - "bph = bottle / hour"
fields:
  - name: production_speed
    description: Nominal production speed.
    type: number
    unit: bph
  - name: machine_category
    description: Type of machine.
    type: enum
    values: [filler, capper]
settings:
  llm:
    model: provider/model
""",
        encoding="utf-8",
    )
    config = load_config(path)
    assert [f.name for f in config.fields] == ["production_speed", "machine_category"]
    assert config.settings.llm.model == "provider/model"


@pytest.mark.parametrize(
    "fields, message",
    [
        ([{"name": "PowerSupply", "description": "x"}], "snake_case"),
        ([{"name": "a", "description": "x"}, {"name": "a", "description": "y"}], "duplicate"),
        ([{"name": "kind", "description": "x", "type": "enum"}], "needs `values`"),
        ([{"name": "kind", "description": "x", "values": ["a"]}], "only for enum"),
        ([{"name": "volt", "description": "x", "unit": "V"}], "only for number"),
        ([{"name": "speed", "description": "x", "type": "number", "unit": "bph"}], "unknown unit"),
    ],
)
def test_invalid_configs(fields, message):
    with pytest.raises(ValidationError, match=message):
        make(fields)


def test_custom_units_resolve():
    config = make(
        [{"name": "speed", "description": "x", "type": "number", "unit": "bph"}],
        units=["bottle = [count]", "bph = bottle / hour"],
    )
    assert config.fields[0].unit == "bph"


def test_hashes_track_what_changes_results():
    base = make([{"name": "a", "description": "x"}])
    same = make([{"name": "a", "description": "x"}])
    other_field = make([{"name": "a", "description": "y"}])
    other_model = make([{"name": "a", "description": "x"}], settings={"llm": {"model": "m"}})
    other_proposals = make(
        [{"name": "a", "description": "x"}], settings={"proposals": {"max_per_document": 3}}
    )
    assert base.schema_hash() == same.schema_hash()
    assert base.schema_hash() != other_field.schema_hash()
    assert base.settings_hash() != other_model.settings_hash()
    assert base.settings_hash() == other_proposals.settings_hash()


def test_provider_routing_is_only_for_openrouter():
    llm = {"model": "anthropic/claude-haiku-5.5", "provider": {"order": ["anthropic"]}}
    with pytest.raises(ValidationError, match="only for openrouter/"):
        make([{"name": "a", "description": "x"}], settings={"llm": llm})


def test_reasoning_and_routing_change_the_settings_hash():
    def llm(**extra):
        settings = {"llm": {"model": "openrouter/qwen/qwen3.8-27b", **extra}}
        return make([{"name": "a", "description": "x"}], settings=settings).settings_hash()

    hashes = {llm(), llm(reasoning_effort="none"), llm(provider={"order": ["deepinfra/bf16"]})}
    assert len(hashes) == 3


def test_unset_new_settings_keep_recorded_hashes():
    golden = ExtractionResult.from_json(ROOT / "corpus/golden/generator/tm-9-6115-642-10.json")
    assert load_config(ROOT / "examples/generator.yaml").settings_hash() == golden.run.settings_hash
