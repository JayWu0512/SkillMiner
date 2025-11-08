# src/core/config.py
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv


# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------

# .../backend/src/core/config.py  → PROJECT_ROOT = .../backend
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
# One level up from the backend/ folder
REPO_ROOT: Path = PROJECT_ROOT.parent

# Load environment variables from <backend>/.env (if present)
ENV_PATH: Path = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


# ------------------------------------------------------------------------------
# Model / retrieval knobs
# ------------------------------------------------------------------------------

MODEL_CHAT: str = os.getenv("MODEL_CHAT", "gpt-4o-mini")
MODEL_EMBED: str = os.getenv("MODEL_EMBED", "text-embedding-3-large")

def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

TOP_K: int = _int_env("TOP_K", 6)

# Context limits (tokens/characters you want to keep)
MAX_RESUME_CTX: int = _int_env("MAX_RESUME_CTX", 4000)
MAX_USER_CTX: int   = _int_env("MAX_USER_CTX", 1200)


# ------------------------------------------------------------------------------
# Dataset / files
# ------------------------------------------------------------------------------

# Default parquet inside the repo:
# <repo>/database/data/gold/role_skills_by_title.parquet
_default_parquet: Path = REPO_ROOT / "database" / "data" / "gold" / "role_skills_by_title.parquet"

# Allow override via DATASET_PATH in .env; coerce env string → Path
DATASET_PATH: Path = Path(os.getenv("DATASET_PATH", str(_default_parquet))).resolve()

# Chroma directory (persistent client path)
CHROMA_DIR: Path = Path(os.getenv("CHROMA_DIR", str(PROJECT_ROOT / "chroma"))).resolve()

# App log file (used by your app if needed)
LOG_FILE: Path = Path(os.getenv("LOG_FILE", str(PROJECT_ROOT / "chat_logs.json"))).resolve()


# ------------------------------------------------------------------------------
# System prompt for the chat agent
# ------------------------------------------------------------------------------

SYSTEM_PROMPT: str = """
You are a data-grounded assistant. Use ONLY the information in the CONTEXT to answer.
If the answer is not in the CONTEXT, say: "You can ask some questions about your resume or the roles."

Rules:
- Cite the relevant row ids or keys from CONTEXT when making claims.
- Never invent facts that aren’t present in CONTEXT.
- If the user asks broadly, summarize what the CONTEXT supports.
- Prefer concise bullet points with concrete fields from the data.
""".strip()


# ------------------------------------------------------------------------------
# Optional: quick self-check utilities (safe to import; no side effects)
# ------------------------------------------------------------------------------

def validate_paths() -> dict[str, bool]:
    """
    Return a dict of key paths and whether they exist on disk.
    Helpful for debugging misconfigured environments.
    """
    return {
        "ENV_PATH_exists": ENV_PATH.exists(),
        "DATASET_PATH_exists": DATASET_PATH.exists(),
        "CHROMA_DIR_exists": CHROMA_DIR.exists(),
        "LOG_FILE_parent_exists": LOG_FILE.parent.exists(),
    }


# What this module exports (helps with from ... import *)
__all__ = [
    "PROJECT_ROOT",
    "REPO_ROOT",
    "ENV_PATH",
    "MODEL_CHAT",
    "MODEL_EMBED",
    "TOP_K",
    "MAX_RESUME_CTX",
    "MAX_USER_CTX",
    "DATASET_PATH",
    "CHROMA_DIR",
    "LOG_FILE",
    "SYSTEM_PROMPT",
    "validate_paths",
]
