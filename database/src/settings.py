from pathlib import Path

# Base folders (relative to project root). Adjust if you run from elsewhere.
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

# Ensure folders exist
for d in [RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# File names for standardized outputs
BRONZE_PATH = BRONZE_DIR / "jobs.parquet"
SILVER_PATH = SILVER_DIR / "jobs_text.parquet"
TOP_SKILLS_PATH = GOLD_DIR / "top_skills.parquet"

# Role filters for this project
TARGET_ROLES = [
    "data scientist",
    "data analyst",
    "data engineer",
    "software engineer",
]

# Add path for the skills link table
ROLE_SKILLS_PATH = GOLD_DIR / "role_skills_by_title.parquet"
