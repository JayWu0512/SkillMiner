# src/infra/exporters/sqlite_exporter.py
from __future__ import annotations

from pathlib import Path
import glob
import json
import sqlite3
from typing import Mapping, Sequence

import polars as pl


class SQLiteMaterializer:
    """
    Materialize selected Parquet sources into a single SQLite database.

    - Supports multiple sources per table via glob patterns.
    - No pandas/pyarrow required: writes directly via sqlite3.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    # ---------- internal utilities ----------

    def _read_parquets(self, patterns: Sequence[str]) -> pl.DataFrame:
        """
        Load one or more Parquet files (glob-supported) and return a Polars DataFrame.
        """
        paths: list[str] = []
        for p in patterns:
            paths.extend(glob.glob(p))
        if not paths:
            raise FileNotFoundError(f"No parquet matched: {patterns}")

        # Lazy-read each file and concatenate vertically
        lf = pl.concat([pl.scan_parquet(p) for p in paths])
        return lf.collect()

    def _normalize_for_sqlite(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Normalize dtypes so SQLite receives friendly types.

        Rules:
        - Categorical -> Utf8 (TEXT)
        - List        -> Utf8 (JSON string)
        - Datetime    -> Utf8 (ISO-8601 string)
        - Object      -> Utf8 (stringified, safe fallback)
        """
        import json

        cols = df.columns
        dtypes = df.dtypes

        # 1) Categorical -> text
        cat_cols = [c for c, t in zip(cols, dtypes) if t.is_(pl.Categorical)]
        if cat_cols:
            df = df.with_columns([pl.col(c).cast(pl.Utf8) for c in cat_cols])

        # 2) List -> JSON string (handle None)
        list_cols = [c for c, t in zip(cols, dtypes) if t.is_(pl.List)]
        for c in list_cols:
            df = df.with_columns(
                pl.col(c).map_elements(
                    lambda v: None if v is None else json.dumps(v, ensure_ascii=False),
                    return_dtype=pl.Utf8,
                )
            )

        # 3) Datetime -> ISO string
        dt_cols = [c for c, t in zip(cols, dtypes) if t.is_(pl.Datetime)]
        if dt_cols:
            df = df.with_columns(
                [pl.col(c).dt.strftime("%Y-%m-%d %H:%M:%S").alias(c) for c in dt_cols]
            )

        # 4) Fallback: if any column is still List/Object, stringify it
        # (covers mixed-typed columns where Polars kept dtype as List/Object)
        # Some polars versions may not have `pl.Object`; guard it.
        try:
            has_object = True
            OBJ = pl.Object
        except AttributeError:
            has_object = False
            OBJ = None  # type: ignore

        # Re-check dtypes after above casts
        cols2 = df.columns
        dtypes2 = df.dtypes

        fallback_cols: list[str] = []
        for c, t in zip(cols2, dtypes2):
            if t.is_(pl.List):
                fallback_cols.append(c)
            elif has_object and t.is_(OBJ):  # type: ignore[arg-type]
                fallback_cols.append(c)

        if fallback_cols:
            df = df.with_columns(
                [
                    pl.col(c)
                    .map_elements(
                        lambda v: (
                            None
                            if v is None
                            else (
                                json.dumps(v, ensure_ascii=False)
                                if isinstance(v, (list, dict))
                                else str(v)
                            )
                        ),
                        return_dtype=pl.Utf8,
                    )
                    .alias(c)
                    for c in fallback_cols
                ]
            )

        return df

    def _sqlite_type(self, dtype: pl.DataType) -> str:
        """
        Map Polars dtypes to SQLite column types.
        (Avoids group aliases like `pl.Integer` so it works across Polars versions.)
        """
        INT_DTYPES = {
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        }
        FLOAT_DTYPES = {pl.Float32, pl.Float64}

        try:
            # Handle Duration/Boolean via .is_ which exists across versions
            if dtype.is_(pl.Duration):
                return "INTEGER"  # store duration as integer (time units)
            if dtype.is_(pl.Boolean):
                return "INTEGER"  # 0/1
            if dtype.is_(pl.Utf8):
                return "TEXT"
        except AttributeError:
            # Fallback if very old Polars – we won't hit this in normal setups
            pass

        # Exact dtype matches (works across versions)
        if dtype in INT_DTYPES:
            return "INTEGER"
        if dtype in FLOAT_DTYPES:
            return "REAL"

        # Default: TEXT (covers Utf8 and any normalized datetime/list already converted)
        return "TEXT"

    def _ensure_table(
        self, conn: sqlite3.Connection, table: str, df: pl.DataFrame, if_exists: str
    ) -> None:
        """
        Create/replace/append a table with schema derived from DataFrame.
        """
        quoted_table = f'"{table}"'

        if if_exists == "replace":
            conn.execute(f"DROP TABLE IF EXISTS {quoted_table}")
        elif if_exists == "fail":
            # if table exists, sqlite will raise on CREATE TABLE
            pass
        elif if_exists == "append":
            # ensure table exists with the same schema; create if not exists
            pass
        else:
            raise ValueError("if_exists must be one of {'fail','replace','append'}")

        # Build CREATE TABLE if not exists
        cols = []
        for name, dtype in zip(df.columns, df.dtypes):
            coltype = self._sqlite_type(dtype)
            cols.append(f'"{name}" {coltype}')
        ddl = f"CREATE TABLE IF NOT EXISTS {quoted_table} ({', '.join(cols)})"
        conn.execute(ddl)

    def _insert_rows(
        self, conn: sqlite3.Connection, table: str, df: pl.DataFrame
    ) -> None:
        """
        Batch insert rows using executemany; aggressively coerce any remaining
        Python types (list/dict/datetime/bool) into SQLite-friendly values.
        """
        from datetime import datetime, date, time

        def _py_coerce(v):
            # NULL stays NULL
            if v is None:
                return None
            # lists/dicts -> JSON string
            if isinstance(v, (list, dict)):
                return json.dumps(v, ensure_ascii=False)
            # booleans -> 0/1
            if isinstance(v, bool):
                return int(v)
            # datetime/date/time -> ISO text
            if isinstance(v, (datetime, date, time)):
                # Use a space between date and time for readability in SQLite
                return v.isoformat(sep=" ") if hasattr(v, "isoformat") else str(v)
            # everything else (int/float/str/bytes) pass through
            return v

        quoted_table = f'"{table}"'
        cols = df.columns
        placeholders = ", ".join(["?"] * len(cols))
        collist = ", ".join([f'"{c}"' for c in cols])
        sql = f"INSERT INTO {quoted_table} ({collist}) VALUES ({placeholders})"

        # Coerce every cell to a SQLite-friendly Python type
        rows = (tuple(_py_coerce(v) for v in row) for row in df.iter_rows())
        conn.executemany(sql, rows)

    # ---------- public API ----------

    def export(
        self,
        table_to_parquet_globs: Mapping[str, Sequence[str]],
        if_exists: str = "replace",
    ) -> None:
        """
        Export multiple parquet sources to different SQLite tables.
        """
        if if_exists not in {"fail", "replace", "append"}:
            raise ValueError("if_exists must be one of {'fail','replace','append'}")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            for table, globs in table_to_parquet_globs.items():
                df = self._read_parquets(globs)
                df = self._normalize_for_sqlite(df)

                # prepare table
                self._ensure_table(conn, table, df, if_exists)

                # insert data
                self._insert_rows(conn, table, df)

                # Optional: indexes on common query columns
                index_candidates = [
                    "id",
                    "job_id",
                    "title",
                    "role",
                    "skill",
                    "company",
                    "posted_at",
                    "date",
                ]
                for col in index_candidates:
                    if col in df.columns:
                        conn.execute(
                            f"CREATE INDEX IF NOT EXISTS idx_{table}_{col} "
                            f'ON "{table}" ("{col}");'
                        )
