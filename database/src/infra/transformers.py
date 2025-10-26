# src/infra/transformers.py
import re
import polars as pl
from ..domain.ports import Transformer


# -------------------------
# 1) Cleaning / normalization
# -------------------------
class CleanJobTransformer(Transformer):
    """Normalize raw columns into a consistent schema and basic typing."""

    def run(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        cols_set = set(lf.collect_schema().names())

        def first_present(cands: list[str]) -> pl.Expr:
            for c in cands:
                if c in cols_set:
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
        work_type_candidates = [
            "work_type",
            "job_type",
            "onsite_remote",
            "onsite_remote_hybrid",
            "employment_type",
            "remote_status",
        ]
        seniority_candidates = ["seniority", "experience_level", "level", "job_level"]

        out = (
            lf
            # 1) candidate column -> standard column
            .with_columns(
                [
                    first_present(title_candidates).cast(pl.Utf8).alias("title"),
                    first_present(company_candidates).cast(pl.Utf8).alias("company"),
                    first_present(location_candidates).cast(pl.Utf8).alias("location"),
                    first_present(posted_candidates).cast(pl.Utf8).alias("posted_raw"),
                    first_present(desc_candidates).cast(pl.Utf8).alias("desc"),
                    first_present(work_type_candidates)
                    .cast(pl.Utf8)
                    .alias("work_type"),
                    first_present(seniority_candidates)
                    .cast(pl.Utf8)
                    .alias("seniority"),
                    first_present(skills_candidates).cast(pl.Utf8).alias("skills_raw"),
                ]
            )
            # 2) add title_lc and posted_at
            .with_columns(
                [
                    pl.when(pl.col("title").is_not_null())
                    .then(pl.col("title").str.to_lowercase())
                    .otherwise(pl.lit(None))
                    .alias("title_lc"),
                    pl.coalesce(
                        [
                            # use UTC to parse first, and then remove timezone
                            pl.col("posted_raw")
                            .str.strptime(pl.Datetime(time_zone="UTC"), strict=False)
                            .dt.replace_time_zone(None),
                            # try to parse no timezome string
                            pl.col("posted_raw").str.strptime(
                                pl.Datetime, strict=False
                            ),
                        ]
                    ).alias("posted_at"),
                ]
            )
            # 3) basic filter
            .filter(pl.col("title").is_not_null() & pl.col("company").is_not_null())
            # 4) skills regularization
            .with_columns(
                [
                    pl.when(
                        pl.col("skills_raw").is_not_null()
                        & (pl.col("skills_raw") != "")
                    )
                    .then(
                        pl.when(pl.col("skills_raw").str.starts_with("["))
                        .then(
                            # Looks like a JSON-ish list -> strip brackets/quotes and split by comma
                            pl.col("skills_raw")
                            .str.replace_all(r"^\s*\[|\]\s*$", "")  # remove [   ]
                            .str.replace_all("'", "")  # remove single quotes
                            .str.replace_all('"', "")  # remove double quotes
                            .str.replace_all(
                                r"\bNone\b", ""
                            )  # remove Python None token
                            .str.split(",")
                        )
                        .otherwise(
                            # Fallback: plain comma-separated string
                            pl.col("skills_raw").str.split(",")
                        )
                    )
                    .otherwise(pl.lit([]))
                    # per-element cleanup: cast->strip->lowercase; drop blanks/"none"
                    .list.eval(
                        pl.element().cast(pl.Utf8).str.strip_chars().str.to_lowercase()
                    )
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
            # 5) final
            .select(
                [
                    "title",
                    "title_lc",
                    "company",
                    "location",
                    "desc",
                    "work_type",
                    "seniority",
                    "posted_at",
                    "skills_list",
                ]
            )
        )
        return out


# -------------------------
# 2) Role filter
# -------------------------
class RoleFilterTransformer(Transformer):
    """Keep only rows whose title matches any of the target roles (regex)."""

    def __init__(self, roles: list[str]):
        self.roles = roles

    def run(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        if not self.roles:
            return lf
        # Build a single regex: \b(role1|role2|role3)\b
        pattern = r"\b(" + "|".join(re.escape(r) for r in self.roles) + r")\b"
        return lf.filter(pl.col("title_lc").str.contains(pattern))


# -------------------------
# 3) Text join for NLP
# -------------------------
class TextJoinTransformer(Transformer):
    """Concatenate title/description/skills into a single text column for NLP."""

    def run(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(
            [
                pl.concat_str(
                    [
                        pl.col("title_lc").fill_null(""),
                        pl.lit(" "),
                        pl.col("desc").fill_null("").str.to_lowercase(),
                        pl.lit(" "),
                        pl.col("skills_list").list.join(" "),
                    ],
                    separator="",
                ).alias("text")
            ]
        ).select(
            [
                "title_lc",
                "company",
                "location",
                "seniority",
                "work_type",
                "posted_at",
                "skills_list",
                "text",
            ]
        )


# -------------------------
# 4) Derive work_type/seniority when missing
# -------------------------
class DeriveWorkTypeTransformer(Transformer):
    def run(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(
            [
                pl.when(pl.col("work_type").is_not_null() & (pl.col("work_type") != ""))
                .then(pl.col("work_type"))
                .otherwise(
                    pl.when(
                        pl.col("text").str.contains(r"\b(remote|work from home|wfh)\b")
                    )
                    .then(pl.lit("remote"))
                    .when(pl.col("text").str.contains(r"\bhybrid\b"))
                    .then(pl.lit("hybrid"))
                    .when(pl.col("text").str.contains(r"\b(on[- ]?site)\b"))
                    .then(pl.lit("onsite"))  # onsite/on-site/on site
                    .otherwise(pl.lit("NA"))
                )
                .alias("work_type")
            ]
        )


class DeriveSeniorityTransformer(Transformer):
    def run(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(
            [
                pl.when(pl.col("seniority").is_not_null() & (pl.col("seniority") != ""))
                .then(pl.col("seniority"))
                .otherwise(
                    pl.when(pl.col("title_lc").str.contains(r"\bintern(ship)?\b"))
                    .then(pl.lit("intern"))
                    .when(pl.col("title_lc").str.contains(r"\bjunior|jr\.?\b"))
                    .then(pl.lit("junior"))
                    .when(pl.col("title_lc").str.contains(r"\bmid(-| )?level\b"))
                    .then(pl.lit("mid"))
                    .when(pl.col("title_lc").str.contains(r"\bsenior|sr\.?\b"))
                    .then(pl.lit("senior"))
                    .when(pl.col("title_lc").str.contains(r"\blead\b"))
                    .then(pl.lit("lead"))
                    .when(pl.col("title_lc").str.contains(r"\b(principal|staff)\b"))
                    .then(pl.lit("principal"))
                    .when(pl.col("title_lc").str.contains(r"\bmanager|mgr\.?\b"))
                    .then(pl.lit("manager"))
                    .otherwise(pl.lit("NA"))
                )
                .alias("seniority")
            ]
        )


class AttachSkillsTransformer(Transformer):
    """
    Attach skills to the main jobs LazyFrame.
    Supports two schemas:
      A) link-table rows:    (job_id, skill_name)   -> aggregate -> join on job_id
      B) already aggregated: (job_link, job_skills) -> direct join on job_link
    Produces 'job_skills' (comma-separated string) so CleanJobTransformer can pick it up.
    """

    def __init__(
        self,
        skills_lf: pl.LazyFrame,
        *,
        on_id: str = "job_id",
        skill_col: str = "skill_name",
        on_link: str = "job_link",
        skills_str_col: str = "job_skills"
    ):
        self.skills_lf = skills_lf  # the raw skills LazyFrame
        self.on_id = on_id  # join key when schema A is present
        self.skill_col = skill_col  # skills value when schema A is present
        self.on_link = on_link  # join key when schema B is present
        self.skills_str_col = (
            skills_str_col  # skills string col when schema B is present
        )

    def run(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        sk_cols = set(self.skills_lf.collect_schema().names())

        if {self.on_link, self.skills_str_col}.issubset(sk_cols):
            # Schema B: (job_link, job_skills) -> direct join on job_link
            return lf.join(
                self.skills_lf.select([self.on_link, self.skills_str_col]),
                on=self.on_link,
                how="left",
            )

        elif {self.on_id, self.skill_col}.issubset(sk_cols):
            # Schema A: (job_id, skill_name) -> aggregate -> join on job_id
            sk_agg = (
                self.skills_lf.group_by(self.on_id)
                .agg(
                    pl.col(self.skill_col)
                    .cast(pl.Utf8)
                    .unique()
                    .sort()
                    .alias("skills_list")
                )
                .with_columns(
                    pl.when(pl.col("skills_list").is_not_null())
                    .then(pl.col("skills_list").list.join(","))
                    .otherwise(pl.lit(None))
                    .alias("job_skills")
                )
                .select([self.on_id, "job_skills"])
            )
            return lf.join(sk_agg, on=self.on_id, how="left")

        else:
            # Unknown schema: return lf unchanged (and you may log a warning if you like)
            return lf
