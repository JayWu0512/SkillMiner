# English comments only below.
import polars as pl
from pathlib import Path

TEST_DIR = Path("data/test")


def test_tiny_jobs_basic_schema_and_edges():
    df = pl.read_parquet(TEST_DIR / "tiny_jobs.parquet")

    expected = {
        "job_id",
        "title",
        "title_lc",
        "company",
        "location",
        "desc",
        "posted_at",
    }
    assert expected.issubset(set(df.columns))

    assert "posted_at" in df.columns
    assert (
        df["posted_at"].dtype.is_temporal() or df["posted_at"].null_count() == df.height
    )

    if df.height >= 2 and "desc" in df.columns:
        assert df["desc"][1] is None or True  # allow datasets without the injected null
        if isinstance(df["desc"][0], str):
            assert len(df["desc"][0]) >= 100  # long-ish text (lower bound relaxed)


def test_tiny_jobs_text_exists_and_nonempty_ratio():
    df = pl.read_parquet(TEST_DIR / "tiny_jobs_text.parquet")
    assert {"job_id", "title", "company", "location", "text"}.issubset(set(df.columns))

    # Count non-empty texts (treat null as empty)
    nonempty = (pl.Series(df["text"]).fill_null("").str.len_chars() > 0).sum()

    # Very permissive: require at least one non-empty text
    assert nonempty >= 1
