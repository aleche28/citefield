"""Extract metadata from technical manuals, with a verifiable citation for every value."""

from importlib.metadata import version

from citefield.config import Config, load_config
from citefield.evaluate import evaluate
from citefield.extraction import Extractor
from citefield.output import ExtractionResult
from citefield.review import apply_review

__version__ = version("citefield")

__all__ = [
    "Config",
    "ExtractionResult",
    "Extractor",
    "__version__",
    "apply_review",
    "evaluate",
    "load_config",
]
