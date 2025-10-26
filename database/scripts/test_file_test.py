import polars as pl
from pathlib import Path

TEST = Path("data/test")

# tiny_jobs
jobs = pl.read_parquet(TEST / "tiny_jobs.parquet")
print(jobs.shape)
print(jobs.columns)
print(jobs.head(5))

# tiny_jobs_text
jobs_text = pl.read_parquet(TEST / "tiny_jobs_text.parquet")
print(jobs_text.shape)
print(jobs_text.columns)
print(jobs_text.head(5))

# tiny_top_skills
skills = pl.read_parquet(TEST / "tiny_top_skills.parquet")
print(skills.shape)
print(skills.columns)
print(skills.head(10))
