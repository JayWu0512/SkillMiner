# Ensure "src/" is importable as a package during tests.
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # project root (the folder containing src/)
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # so "import src" works
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))  # (optional) direct "from infra import ..." patterns
