import os
import re
import sys
from pathlib import Path

import pytest

# LiteLLM downloads its model map from GitHub on import unless told not to; tests stay offline
# and get the same context windows on every run.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

sys.path.insert(0, str(Path(__file__).parent))


PROVIDER_VAR = re.compile(r"_API_(KEY|BASE|VERSION)$|^AZURE_")


@pytest.fixture(autouse=True)
def no_provider_credentials(request, monkeypatch):
    """Clear API keys and endpoints, so tests run the same here and in CI; not for live tests."""
    if request.node.get_closest_marker("live"):
        return
    for name in list(os.environ):
        if PROVIDER_VAR.search(name):
            monkeypatch.delenv(name)
