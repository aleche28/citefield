import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_docs.py"


def test_docs_are_consistent():
    result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
