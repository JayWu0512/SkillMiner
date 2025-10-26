# English comments only below.
import polars as pl
from pathlib import Path
from src.infra.transformers import (
    TextJoinTransformer,
    DeriveWorkTypeTransformer,
    DeriveSeniorityTransformer,
)

TEST_DIR = Path("data/test")


def test_end_to_end_small_pipeline():
    lf = pl.read_parquet(TEST_DIR / "tiny_jobs.parquet").lazy()

    # Ensure required columns exist before TextJoin selects them.
    # TextJoin selects 'seniority' and 'work_type', so create them if missing.
    schema = set(lf.collect_schema().names())
    if "work_type" not in schema or "seniority" not in schema:
        lf = lf.with_columns(
            [
                (
                    (pl.lit(None).cast(pl.Utf8)).alias("work_type")
                    if "work_type" not in schema
                    else pl.col("work_type")
                ),
                (
                    (pl.lit(None).cast(pl.Utf8)).alias("seniority")
                    if "seniority" not in schema
                    else pl.col("seniority")
                ),
            ]
        )

    lf = TextJoinTransformer().run(lf)
    lf = DeriveWorkTypeTransformer().run(lf)
    lf = DeriveSeniorityTransformer().run(lf)
    out = lf.collect()

    assert out.height > 0
    assert {
        "title_lc",
        "company",
        "location",
        "text",
        "work_type",
        "seniority",
    }.issubset(set(out.columns))
    # Sanity: at least a few texts are non-empty
    assert (out["text"].str.len_chars() > 0).sum() >= max(1, int(0.001 * out.height))
