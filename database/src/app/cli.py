import typer
from pathlib import Path

from .pipeline import JobsPipeline
from src.infra.exporters.sqlite_exporter import SQLiteMaterializer

app = typer.Typer()


@app.command()
def build():
    """Run the ETL pipeline."""
    JobsPipeline().build()
    typer.echo("Build completed.")


@app.command("export-sqlite")
def export_sqlite(
    db: str = typer.Option(
        "database/skillminer.db", help="Path to the output SQLite file"
    ),
    silver_jobs: str = typer.Option(
        "data/silver/jobs_text.parquet", help="Path or glob for the silver Parquet"
    ),
    gold_role_skills: str = typer.Option(
        "data/gold/role_skills_by_title.parquet",
        help="Path or glob for the gold Parquet",
    ),
):
    """
    Materialize selected Parquet files (silver/gold) into a single SQLite database.
    Each source is written as a separate table.
    """
    tables = {
        "jobs_text": [silver_jobs],
        "role_skills_by_title": [gold_role_skills],
    }

    SQLiteMaterializer(Path(db)).export(tables)
    typer.echo(f"Exported tables {list(tables.keys())} → {db}")


if __name__ == "__main__":
    app()
