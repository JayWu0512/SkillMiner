import polars as pl
from ..domain.ports import Aggregator


class TopSkillsAggregator(Aggregator):
    def __init__(self, topk: int = 40):
        self.topk = topk

    def aggregate(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return (
            lf.select(["skills_list"])
            .explode("skills_list")
            .filter(pl.col("skills_list").is_not_null() & (pl.col("skills_list") != ""))
            .group_by("skills_list")
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(self.topk)
        )


class RoleSkillsAggregator:
    """Aggregate per-role skills into a unique/sorted list."""

    def aggregate(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        # expects columns: title_lc, skills_list
        return (
            lf.select(["title_lc", "skills_list"])
            .explode("skills_list")  # one row per (role, skill)
            .drop_nulls("skills_list")
            .group_by("title_lc")
            .agg(
                pl.col("skills_list")
                .unique()
                .sort()
                .alias("skills_for_role")  # list[str]
            )
        )


class RoleSkillCountsAggregator:
    """Aggregate counts of each skill within each role (long format)."""

    def aggregate(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return (
            lf.select(["title_lc", "skills_list"])
            .explode("skills_list")
            .drop_nulls("skills_list")
            .group_by(["title_lc", "skills_list"])
            .agg(pl.len().alias("count"))
            .rename({"skills_list": "skill"})
        )
