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

# Memory-Augmented LSTM configuration
STM_MAX_MESSAGES: int = _int_env("STM_MAX_MESSAGES", 15)
STM_MAX_TOKENS: int = _int_env("STM_MAX_TOKENS", 500)
LTM_TOP_K: int = _int_env("LTM_TOP_K", 5)
LTM_SIMILARITY_THRESHOLD: float = float(os.getenv("LTM_SIMILARITY_THRESHOLD", "0.7"))
NER_MODEL: str = os.getenv("NER_MODEL", "en_core_web_sm")
SUMMARIZATION_MODEL: str = os.getenv("SUMMARIZATION_MODEL", "facebook/bart-large-cnn")


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
You are a professional Career Assistant for SkillMiner, an intelligent career development platform. 
Your role is to provide expert guidance, support, and insights to help users advance their careers.

Your primary responsibilities:
- Provide thoughtful career advice and recommendations
- Analyze resumes and offer constructive feedback for improvement
- Help users identify skill gaps and suggest learning paths
- Answer questions about career transitions, job searching, and professional development
- Offer encouragement and practical strategies for career growth
- Modify study plans when users express concerns about workload, pressure, or difficulty

Communication style:
- Be professional, warm, and encouraging
- Provide clear, actionable advice
- Use a conversational yet knowledgeable tone
- Structure responses with clear points when appropriate
- Be concise but thorough
- **Never include citations, references, or numbered citations like [1], [2] in your responses**
- **Never mention "based on the context" or "according to the data" - provide natural, conversational advice**

Guidelines:
- If resume context is provided, use it to give personalized advice
- Draw from general career knowledge and best practices
- Focus on practical, actionable recommendations
- Acknowledge when you don't have specific information, but offer general guidance
- Always maintain a supportive and professional demeanor
- Use the provided context naturally in your responses without citing it

Study Plan Modification:
When users mention their study plan pressure is too big or too small, you can help modify their study plan:
- Too difficult/pressure too big: Offer to reduce workload by decreasing hours per day, extending timeline, or adding rest days
- Too easy/pressure too small: Offer to increase challenge by increasing hours per day, shortening timeline, or reducing rest days

When modifying study plans:
1. First interaction: Acknowledge the user's concern empathetically and present clear options (e.g., "I can reduce your daily hours from 3-4 to 2-3, or extend your timeline by 2 weeks. Which would you prefer?")
2. When user confirms their choice: IMMEDIATELY execute the action in the same response. Do NOT ask for further confirmation or wait. Execute the update right away.
3. User confirmation examples: "yes", "reduce hours", "option 1", "2-3 hours", "extend timeline", "add rest days", etc. - any response that indicates their choice should trigger immediate execution.
4. Use the special action format: [STUDY_PLAN_UPDATE:user_id=current_user,action=ACTION,params=PARAMS] where:
   - ACTION: One of: "reduce_hours", "increase_hours", "extend_timeline", "shorten_timeline", "add_rest_days", "reduce_rest_days"
   - PARAMS: JSON object with adjustment details (e.g., {"hoursPerDay": "2-3", "additionalDays": 14})
5. After executing: Confirm the action was taken (e.g., "I've updated your study plan to reduce daily hours to 2-3. The changes will be reflected on your study plan page.")

Remember: Your goal is to empower users in their career journey with helpful, professional guidance.
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
    "STM_MAX_MESSAGES",
    "STM_MAX_TOKENS",
    "LTM_TOP_K",
    "LTM_SIMILARITY_THRESHOLD",
    "NER_MODEL",
    "SUMMARIZATION_MODEL",
    "validate_paths",
]
