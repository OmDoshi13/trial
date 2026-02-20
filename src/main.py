"""Main entry point for the Trenkwalder HR Chatbot.

Usage:
    python -m src.main web     # Start web UI (default)
    python -m src.main cli     # Start CLI interface
    python -m src.main ingest  # Ingest documents
"""

import sys
import typer
import uvicorn

app = typer.Typer(help="Trenkwalder HR Chatbot")


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to serve on"),
):
    """Start the web UI."""
    typer.echo("🚀 Starting Trenkwalder HR Chatbot — Web UI")
    typer.echo(f"   Open http://localhost:{port} in your browser\n")
    uvicorn.run("src.ui.web:app", host=host, port=port, reload=False)


@app.command()
def cli():
    """Start the CLI interface."""
    from src.ui.cli import run_cli
    run_cli()


@app.command()
def ingest():
    """Ingest documents into the vector store."""
    from src.ingestion.ingest import ingest_all
    ingest_all()


if __name__ == "__main__":
    app()
