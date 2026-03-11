"""Click CLI entry point for Genesis Navigator.

Usage::

    genesis-nav [ROOT_DIR] [--port PORT] [--no-browser]

Validates ROOT_DIR, configures the FastAPI app, optionally opens a browser,
then blocks on uvicorn until Ctrl-C.
"""

# Implements: REQ-F-API-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

import webbrowser
from pathlib import Path

import click
import uvicorn

import genesis_nav.main as _main


@click.command()
@click.argument(
    "root_dir",
    default=".",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--port",
    default=8765,
    show_default=True,
    help="TCP port for the API server.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Do not open a browser tab automatically.",
)
def main(root_dir: Path, port: int, no_browser: bool) -> None:
    """Start Genesis Navigator pointing at ROOT_DIR (default: current directory).

    The backend API will be available at http://localhost:PORT.

    Args:
        root_dir: Root directory to scan for Genesis projects.
        port: TCP port for uvicorn.
        no_browser: When True, suppress automatic browser launch.
    """
    root_dir = root_dir.resolve()

    # Inject config into app module before uvicorn starts (avoids env-var coupling)
    _main._config["root_dir"] = str(root_dir)

    url = f"http://localhost:{port}"
    click.echo(f"Genesis Navigator — scanning: {root_dir}")
    click.echo(f"API: {url}/docs")

    if not no_browser:
        # Non-blocking open; uvicorn may not be ready yet but the browser will
        # retry or the user can refresh once the server is up.
        webbrowser.open(url)

    uvicorn.run(
        "genesis_nav.main:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )
