from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

# Models / knobs
MODEL_CHAT = os.getenv("MODEL_CHAT", "gpt-4o-mini")
MODEL_EMBED = os.getenv("MODEL_EMBED", "text-embedding-3-large")
TOP_K = int(os.getenv("TOP_K", "6"))

# Context limits
MAX_RESUME_CTX = 4000
MAX_USER_CTX = 1200

# Files / paths
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", PROJECT_ROOT / "chroma"))
LOG_FILE = Path(os.getenv("LOG_FILE", PROJECT_ROOT / "chat_logs.json"))

# Prompt
SYSTEM_PROMPT = """
You are a data-grounded assistant. Use ONLY the information in the CONTEXT to answer.
If the answer is not in the CONTEXT, say: "You can ask some questions about your resume or the roles."

Rules:
- Cite the relevant row ids or keys from CONTEXT when making claims.
- Never invent facts that aren’t present in CONTEXT.
- If the user asks broadly, summarize what the CONTEXT supports.
- Prefer concise bullet points with concrete fields from the data.
"""
