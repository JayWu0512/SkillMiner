# src/infra/io_polars.py
import polars as pl
from typing import List
from ..domain.ports import DatasetRepository


def _schema_names(lf: pl.LazyFrame) -> list[str]:
    return lf.collect_schema().names()


class PolarsLocalRepository(DatasetRepository):
    def load_many(self, paths: List[str]) -> pl.LazyFrame:
        if not paths:
            raise ValueError("No input files provided.")

        lfs = [pl.scan_parquet(p) for p in paths]

        # --- UNION of columns (not intersection) ---
        all_cols = sorted({name for lf in lfs for name in _schema_names(lf)})

        # Add missing columns as nulls so all frames align by name
        aligned = []
        for lf in lfs:
            names = set(_schema_names(lf))
            # add missing columns as nulls
            lf_aug = lf.with_columns(
                *[pl.lit(None).alias(c) for c in all_cols if c not in names]
            ).select(all_cols)
            aligned.append(lf_aug)

        # Robust concat; rechunk for downstream perf
        return pl.concat(aligned, how="diagonal_relaxed", rechunk=True)

    def save_lazy(self, table: pl.LazyFrame | pl.DataFrame, path: str) -> None:
        if isinstance(table, pl.LazyFrame):
            table.sink_parquet(path)
        else:
            table.write_parquet(path)
