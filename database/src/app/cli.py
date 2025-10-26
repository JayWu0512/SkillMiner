import typer
from .pipeline import JobsPipeline

app = typer.Typer()


@app.command()
def build():
    """Build pipeline."""
    JobsPipeline().build()
    typer.echo("build done.")


if __name__ == "__main__":
    app()
