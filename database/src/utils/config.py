from pathlib import Path
from typing import List


def ensure_dirs(*dirs: Path) -> None:
    """Create directories if they do not exist."""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def list_parquet_files(folder: Path) -> List[Path]:
    """Return all .parquet files under a folder (non-recursive)."""
    return sorted(folder.glob("*.parquet"))
