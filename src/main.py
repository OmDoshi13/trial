"""Entry point — start the web server, CLI, or run ingestion."""

import sys
import threading
import typer
import uvicorn

app = typer.Typer(help="Trenkwalder HR Chatbot")


def _start_mock_hr_service():
    """Run the mock HR API on port 8001 in a daemon thread."""
    from src.tools.mock_hr_service import mock_app
    uvicorn.run(mock_app, host="0.0.0.0", port=8001, log_level="warning")


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to serve on"),
):
    """Start the web UI (also launches the mock HR service)."""
    typer.echo("🚀 Starting Trenkwalder HR Chatbot — Web UI")
    typer.echo("   Mock HR service on http://localhost:8001")
    typer.echo(f"   Chat UI on http://localhost:{port}\n")

    # Start mock HR service as a background daemon thread
    hr_thread = threading.Thread(target=_start_mock_hr_service, daemon=True)
    hr_thread.start()

    uvicorn.run("src.ui.web:app", host=host, port=port, reload=False)


@app.command()
def cli():
    """Start the CLI interface (also launches the mock HR service)."""
    hr_thread = threading.Thread(target=_start_mock_hr_service, daemon=True)
    hr_thread.start()
    from src.ui.cli import run_cli
    run_cli()


@app.command()
def ingest():
    """Ingest documents into the vector store."""
    from src.ingestion.ingest import ingest_all
    ingest_all()


if __name__ == "__main__":
    app()
