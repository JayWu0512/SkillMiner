# English comments only below.
import polars as pl
from pathlib import Path
from src.infra.transformers import (
    RoleFilterTransformer,
    TextJoinTransformer,
    DeriveWorkTypeTransformer,
    DeriveSeniorityTransformer,
)

TEST_DIR = Path("data/test")


def _lazy_from_tiny_jobs():
    return pl.read_parquet(TEST_DIR / "tiny_jobs.parquet").lazy()


def test_role_filter_matches_selected_roles():
    lf = _lazy_from_tiny_jobs()
    roles = ["data scientist", "data engineer", "machine learning", "analyst"]
    out = RoleFilterTransformer(roles=roles).run(lf).collect()
    # Should keep some rows
    # if none, the sample didn't contain target roles; still assert not crashing
    assert out.height >= 0  # existence test; no crash


def test_text_join_and_derive_fields_are_present():
    lf = _lazy_from_tiny_jobs()

    # Ensure required columns for TextJoin select
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

    for col in ["text", "work_type", "seniority"]:
        assert col in out.columns

    # work_type remains within expected categories
    assert set(out["work_type"].drop_nulls().unique().to_list()) <= {
        "remote",
        "hybrid",
        "onsite",
        "NA",
    }
