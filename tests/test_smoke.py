import citefield
from citefield.cli import main
from citefield.config import Config


def test_version():
    assert citefield.__version__


def test_config_defaults():
    config = Config(
        fields=[{"name": "power_supply_voltage", "description": "Mains supply voltage."}]
    )
    assert config.settings.parser == "pdfplumber"
    assert config.settings.extraction.field_batch_size == 30


def test_cli_stub_exits_nonzero():
    assert main(["validate-config", "fields.yaml"]) == 2
