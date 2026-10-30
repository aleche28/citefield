import os
import sys
from pathlib import Path

# LiteLLM downloads its model map from GitHub on import unless told not to; tests stay offline
# and get the same context windows on every run.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

sys.path.insert(0, str(Path(__file__).parent))
