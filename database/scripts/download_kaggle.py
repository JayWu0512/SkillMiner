# scripts/download_kaggle.py

import kagglehub
import polars as pl
from pathlib import Path

LINK = "asaniczka/1-3m-linkedin-jobs-and-skills-2024"


def download_datasets(dataset: str, out_dir: str | Path):
    # Download Kaggle dataset (returns a local directory path)
    path = kagglehub.dataset_download(dataset)
    data_dir = Path(path)

    # Ensure output directory exists
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Convert all CSV files in the dataset folder to Parquet
    for csv_file in data_dir.glob("*.csv"):
        parquet_file = out_dir / (csv_file.stem + ".parquet")
        print(f"Converting {csv_file} -> {parquet_file}")

        # Use Polars Lazy API (streaming), with safer options
        (
            pl.scan_csv(
                csv_file,
                has_header=True,
                ignore_errors=True,
                infer_schema_length=1000,
                low_memory=True,
            ).sink_parquet(parquet_file, statistics=True, compression="zstd")
        )

    return out_dir


if __name__ == "__main__":
    out = download_datasets(dataset=LINK, out_dir="data/raw")
    print("All CSV converted to Parquet under:", out)
