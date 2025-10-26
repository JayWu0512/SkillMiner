# scripts/make_test_data.py
from __future__ import annotations

import argparse
import os
import pathlib
import random
import sys
from typing import Iterable, Optional, List

import polars as pl

# -------------------------
# Paths & constants
# -------------------------
PROJ = pathlib.Path(__file__).resolve().parents[1]
RAW = PROJ / "data" / "raw"
OUT = PROJ / "data" / "test"

# Defaults kept tiny to stay well under GitHub limits
DEFAULT_SEED = int(os.getenv("TINY_SEED", 42))
DEFAULT_N_PER_GROUP = int(os.getenv("TINY_N_PER_GROUP", 2))  # rows per group
DEFAULT_MAX_ROWS = int(os.getenv("TINY_MAX_ROWS", 2000))  # global cap
DEFAULT_GEN_TOP_SKILLS = os.getenv("TINY_GEN_TOP_SKILLS", "1")  # "1" to enable

random.seed(DEFAULT_SEED)
OUT.mkdir(parents=True, exist_ok=True)

# Ensure project src on sys.path (future-proof)
if str(PROJ / "src") not in sys.path:
    sys.path.append(str(PROJ / "src"))


# -------------------------
# Helpers
# -------------------------
def stratified_sample(
    df: pl.DataFrame, by: str, n_per_group: int, seed: int
) -> pl.DataFrame:
    """Stratified sampling: take up to n_per_group rows from each group."""
    if by not in df.columns:
        raise ValueError(
            f'Stratified sample "by" column "{by}" not found. Available: {df.columns}'
        )
    return (
        df.with_columns(pl.int_range(0, pl.len()).shuffle(seed=seed).alias("__rand__"))
        .with_columns(pl.col("__rand__").rank("ordinal").over(by).alias("__rk__"))
        .filter(pl.col("__rk__") <= n_per_group)
        .drop(["__rand__", "__rk__"])
    )


def read_if_exists(path: pathlib.Path) -> Optional[pl.LazyFrame]:
    """Return a LazyFrame if parquet exists, else None."""
    return pl.scan_parquet(path) if path.exists() else None


def normalize_lazy(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Normalize raw columns into a consistent schema:
      job_id, job_link, title, title_lc, company, location, desc, posted_at, skills_list

    This is a lightweight/standalone version aligned with your CleanJobTransformer.
    It inspects the *source* schema first to pick best-matching columns.
    """
    schema_names = set(lf.collect_schema().names())

    def pick(cands: Iterable[str]) -> pl.Expr:
        for c in cands:
            if c in schema_names:
                return pl.col(c)
        return pl.lit(None)

    title_candidates = ["job_title", "title", "position"]
    company_candidates = ["company", "company_name", "employer"]
    location_candidates = ["location", "job_location", "city"]
    posted_candidates = [
        "posted_time",
        "posted_at",
        "date_posted",
        "post_date",
        "first_seen",
        "last_processed_time",
        "created_at",
        "timestamp",
    ]
    desc_candidates = ["description", "job_description", "desc", "job_summary"]
    skills_candidates = ["skills", "skill_list", "tags", "job_skills"]
    jobid_candidates = ["job_id", "id", "jobkey", "posting_id"]
    joblink_candidates = ["job_link", "job_url", "link", "url"]

    # 1) map source columns -> normalized columns
    lf = lf.with_columns(
        [
            pick(title_candidates).cast(pl.Utf8).alias("title"),
            pick(company_candidates).cast(pl.Utf8).alias("company"),
            pick(location_candidates).cast(pl.Utf8).alias("location"),
            pick(posted_candidates).cast(pl.Utf8).alias("posted_raw"),
            pick(desc_candidates).cast(pl.Utf8).alias("desc"),
            pick(skills_candidates).cast(pl.Utf8).alias("skills_raw"),
            pick(jobid_candidates).alias("job_id"),
            pick(joblink_candidates).cast(pl.Utf8).alias("job_link"),
        ]
    )

    # 2) derive title_lc & posted_at
    lf = lf.with_columns(
        [
            pl.when(pl.col("title").is_not_null())
            .then(pl.col("title").str.to_lowercase())
            .otherwise(pl.lit(None))
            .alias("title_lc"),
            pl.coalesce(
                [
                    pl.col("posted_raw")
                    .str.strptime(pl.Datetime(time_zone="UTC"), strict=False)
                    .dt.replace_time_zone(None),
                    pl.col("posted_raw").str.strptime(pl.Datetime, strict=False),
                ]
            ).alias("posted_at"),
        ]
    )

    # 3) normalize skills as list[str] -- no json_decode for broad compatibility
    lf = lf.with_columns(
        [
            pl.when(pl.col("skills_raw").is_not_null() & (pl.col("skills_raw") != ""))
            .then(
                pl.when(pl.col("skills_raw").str.starts_with("["))
                .then(
                    pl.col("skills_raw")
                    .str.replace_all(r"^\s*\[|\]\s*$", "")  # remove brackets
                    .str.replace_all("'", "")  # remove single quotes
                    .str.replace_all('"', "")  # remove double quotes
                    .str.replace_all(r"\bNone\b", "")  # remove Python None token
                    .str.split(",")
                )
                .otherwise(pl.col("skills_raw").str.split(","))
            )
            .otherwise(pl.lit([]))
            .list.eval(pl.element().cast(pl.Utf8).str.strip_chars().str.to_lowercase())
            .list.eval(
                pl.when((pl.element() == "") | (pl.element() == "none"))
                .then(pl.lit(None))
                .otherwise(pl.element())
            )
            .list.drop_nulls()
            .list.unique()
            .alias("skills_list")
        ]
    )

    # 4) final projection + basic filtering
    lf = lf.select(
        [
            "job_id",
            "job_link",
            "title",
            "title_lc",
            "company",
            "location",
            "desc",
            "posted_at",
            "skills_list",
        ]
    ).filter(pl.col("title").is_not_null() & pl.col("company").is_not_null())

    return lf


def write_parquet(df: pl.DataFrame, path: pathlib.Path) -> None:
    """Write parquet with reasonable compression."""
    df.write_parquet(path, compression="zstd")


# -------------------------
# Main
# -------------------------
def main() -> None:
    # CLI args (override env defaults)
    ap = argparse.ArgumentParser(description="Build tiny test parquet files.")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--n-per-group", type=int, default=DEFAULT_N_PER_GROUP)
    ap.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    ap.add_argument(
        "--gen-top-skills",
        type=int,
        default=int(DEFAULT_GEN_TOP_SKILLS),
        help="1 to generate tiny_top_skills.parquet; 0 to skip.",
    )
    args = ap.parse_args()

    # Load raw sources (each may or may not exist)
    job_summary = read_if_exists(RAW / "job_summary.parquet")
    linkedin_posts = read_if_exists(RAW / "linkedin_job_postings.parquet")
    job_skills_lf = read_if_exists(RAW / "job_skills.parquet")

    if job_summary is None and linkedin_posts is None:
        raise FileNotFoundError(
            "No job postings found under data/raw/. Expected one of: "
            "job_summary.parquet or linkedin_job_postings.parquet"
        )

    # Normalize each source first to align schema, then concat
    normalized_sources: List[pl.LazyFrame] = []
    for src in (job_summary, linkedin_posts):
        if src is not None:
            normalized_sources.append(normalize_lazy(src))

    base_norm = (
        normalized_sources[0]
        if len(normalized_sources) == 1
        else pl.concat(normalized_sources, how="vertical")
    )

    # Attach job_skills BEFORE collect (keep it lazy)
    if job_skills_lf is not None:
        sk_cols = set(job_skills_lf.collect_schema().names())
        if {"job_link", "job_skills"}.issubset(sk_cols):
            # left-join via job_link; fill skills_list if empty
            base_norm = (
                base_norm.join(
                    job_skills_lf.select(["job_link", "job_skills"]),
                    on="job_link",
                    how="left",
                )
                .with_columns(
                    pl.when(
                        pl.coalesce([pl.col("skills_list").list.len(), pl.lit(0)]) > 0
                    )
                    .then(pl.col("skills_list"))
                    .otherwise(
                        pl.when(
                            pl.col("job_skills").is_not_null()
                            & (pl.col("job_skills") != "")
                        )
                        .then(
                            pl.col("job_skills")
                            .str.split(",")
                            .list.eval(
                                pl.element()
                                .cast(pl.Utf8)
                                .str.strip_chars()
                                .str.to_lowercase()
                            )
                        )
                        .otherwise(pl.lit([]))
                    )
                    .alias("skills_list")
                )
                .drop("job_skills")
            )
        # (If a different schema appears (e.g., job_id/skill), add a branch here.)

    # Collect to DataFrame for sampling
    jobs_df = base_norm.collect()

    if (
        "title_lc" not in jobs_df.columns
        or jobs_df["title_lc"].null_count() == jobs_df.height
    ):
        raise ValueError(
            "No usable title/title_lc found after normalization. "
            "Check your raw files' column names."
        )

    # Prefer title_lc for grouping
    by_col = "title_lc" if "title_lc" in jobs_df.columns else "title"

    # Stratified sample to keep diversity, then apply a global cap
    tiny_jobs = stratified_sample(
        jobs_df, by=by_col, n_per_group=args.n_per_group, seed=args.seed
    )
    if tiny_jobs.height > args.max_rows:
        tiny_jobs = tiny_jobs.head(args.max_rows)

    # Inject edge cases on 'desc' if possible
    if "desc" in tiny_jobs.columns and tiny_jobs.height >= 2:
        long_text = "lorem ipsum " * 500  # long description to test downstream limits
        tiny_jobs = tiny_jobs.with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(pl.lit(long_text))
            .when(pl.arange(0, pl.len()) == 1)
            .then(pl.lit(None))  # set NULL on row 1
            .otherwise(pl.col("desc"))
            .alias("desc")
        )

    # === NEW: build "role -> skills list" table for testing ===
    # One row per role (title_lc) with a unique/sorted list of skills.
    job_skills_by_role = (
        tiny_jobs.select(["title_lc", "skills_list"])
        .explode("skills_list")  # one row per (role, skill)
        .drop_nulls("skills_list")
        .group_by("title_lc")
        .agg(
            pl.col("skills_list").unique().sort().alias("skills_for_role")  # list[str]
        )
    )

    # Silver-ish: compact text view
    jobs_text = tiny_jobs.select(
        [
            "job_id",
            "title",
            "company",
            "location",
            pl.col("desc").fill_null("").str.to_lowercase().alias("text"),
        ]
    )

    # Optional: build global top_skills
    if args.gen_top_skills:
        if job_skills_lf is not None and "job_id" in tiny_jobs.columns:
            tiny_ids = set(tiny_jobs["job_id"].drop_nulls().to_list())
            skills_df = job_skills_lf.collect()
            if {"job_id", "skill"}.issubset(skills_df.columns):
                tiny_sk = skills_df.filter(pl.col("job_id").is_in(list(tiny_ids)))
                top_skills = (
                    tiny_sk.group_by("skill")
                    .agg(pl.len().alias("count"))
                    .sort(pl.col("count"), descending=True)
                )
            else:
                top_skills = (
                    tiny_jobs.with_columns(pl.col("skills_list").alias("skill"))
                    .explode("skill")
                    .drop_nulls("skill")
                    .group_by("skill")
                    .agg(pl.len().alias("count"))
                    .sort(pl.col("count"), descending=True)
                )
        else:
            top_skills = (
                tiny_jobs.with_columns(pl.col("skills_list").alias("skill"))
                .explode("skill")
                .drop_nulls("skill")
                .group_by("skill")
                .agg(pl.len().alias("count"))
                .sort(pl.col("count"), descending=True)
            )
    else:
        top_skills = pl.DataFrame(
            {"skill": pl.Series([], pl.Utf8), "count": pl.Series([], pl.Int64)}
        )

    # Write tiny test files (always small due to caps)
    write_parquet(tiny_jobs, OUT / "tiny_jobs.parquet")
    write_parquet(jobs_text, OUT / "tiny_jobs_text.parquet")
    write_parquet(top_skills, OUT / "tiny_top_skills.parquet")
    # NEW output: role -> skills list
    write_parquet(job_skills_by_role, OUT / "tiny_job_skills_by_role.parquet")

    print(
        "✅ Wrote (capped):\n"
        f"  - {OUT/'tiny_jobs.parquet'}  (rows={tiny_jobs.height})\n"
        f"  - {OUT/'tiny_jobs_text.parquet'}  (rows={jobs_text.height})\n"
        f"  - {OUT/'tiny_top_skills.parquet'}  (rows={top_skills.height})\n"
        f"  - {OUT/'tiny_job_skills_by_role.parquet'}  (rows={job_skills_by_role.height})"
    )


if __name__ == "__main__":
    main()
