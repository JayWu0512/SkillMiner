# src/app/pipeline.py
import polars as pl
from ..utils.config import ensure_dirs, list_parquet_files
from ..settings import (
    RAW_DIR,
    BRONZE_DIR,
    SILVER_DIR,
    GOLD_DIR,
    BRONZE_PATH,
    SILVER_PATH,
    TOP_SKILLS_PATH,
    TARGET_ROLES,
    ROLE_SKILLS_PATH,
)
from ..infra.io_polars import PolarsLocalRepository
from ..infra.transformers import (
    CleanJobTransformer,
    RoleFilterTransformer,
    TextJoinTransformer,
    DeriveWorkTypeTransformer,
    DeriveSeniorityTransformer,
)
from ..infra.aggregators import TopSkillsAggregator
from ..infra.aggregators import RoleSkillsAggregator


class JobsPipeline:
    """Orchestrates raw -> bronze -> silver -> gold tables."""

    def __init__(self):
        self.repo = PolarsLocalRepository()
        self.cleaner = CleanJobTransformer()
        self.role_filter = RoleFilterTransformer(TARGET_ROLES)
        self.texter = TextJoinTransformer()
        self.topskills = TopSkillsAggregator(topk=40)
        self.worktype = DeriveWorkTypeTransformer()
        self.seniority = DeriveSeniorityTransformer()
        self.role_skills = RoleSkillsAggregator()

    def build(self) -> None:
        """Run the end-to-end table build with whatever is in data/raw."""
        ensure_dirs(BRONZE_DIR, SILVER_DIR, GOLD_DIR)

        # 1) Load all raw parquet files EXCEPT the skills link-table
        raw_paths = list_parquet_files(RAW_DIR)
        raw_files = [str(p) for p in raw_paths if p.name != "job_skills.parquet"]
        if not raw_files:
            raise FileNotFoundError(f"No .parquet files found in {RAW_DIR}")

        lf = self.repo.load_many(raw_files)

        # 1.5) Attach skills BEFORE cleaning (handle both schemas):
        #   A) link-table rows: (job_id, skill_name)  -> aggregate then join
        #   B) already aggregated: (job_link, job_skills) -> direct join on job_link
        skills_path = RAW_DIR / "job_skills.parquet"
        if skills_path.exists():
            sk = pl.scan_parquet(str(skills_path))
            sk_cols = set(sk.collect_schema().names())

            if {"job_id", "skill_name"}.issubset(sk_cols):
                # Schema A: aggregate per job_id then join; produce job_skills string
                sk_agg = (
                    sk.group_by("job_id")
                    .agg(
                        pl.col("skill_name")
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
                    .select(["job_id", "job_skills"])
                )
                # Choose a join key present in your main tables; adjust if needed
                # If your main tables also have 'job_id', join on 'job_id':
                if "job_id" in set(lf.collect_schema().names()):
                    lf = lf.join(sk_agg, on="job_id", how="left")
                else:
                    # Fallback: if main tables use 'job_link' as key, you need a mapping table.
                    # (Most users won't hit this branch; adapt if your raw has 'job_link' only.)
                    pass

            elif {"job_link", "job_skills"}.issubset(sk_cols):
                # Schema B: skills already aggregated as a comma-separated string
                lf = lf.join(
                    sk.select(["job_link", "job_skills"]),
                    on="job_link",
                    how="left",
                )
            else:
                print(
                    f"[warn] Unknown skills schema {sorted(sk_cols)}. "
                    "Skipping skills attachment."
                )

        # 2) Clean/normalize -> bronze
        lf_bronze = self.cleaner.run(lf)
        self.repo.save_lazy(lf_bronze, str(BRONZE_PATH))

        # 3) Role filter + text join + derivations -> silver
        lf_silver = self.role_filter.run(lf_bronze)
        lf_silver = self.texter.run(lf_silver)
        lf_silver = self.worktype.run(lf_silver)
        lf_silver = self.seniority.run(lf_silver)
        self.repo.save_lazy(lf_silver, str(SILVER_PATH))

        # 4) Top skills aggregate -> gold
        lf_top = self.topskills.aggregate(lf_silver)
        self.repo.save_lazy(lf_top, str(TOP_SKILLS_PATH))

        # 5) Role -> skills list -> gold (per-role)
        lf_role_skills = self.role_skills.aggregate(lf_silver)
        self.repo.save_lazy(lf_role_skills, str(ROLE_SKILLS_PATH))

        # Optional: small console hints (no heavy collect)
        print(f"Bronze written: {BRONZE_PATH}")
        print(f"Silver written: {SILVER_PATH}")
        print(f"Top skills written: {TOP_SKILLS_PATH}")
        print(f"Role->skills written: {ROLE_SKILLS_PATH}")
