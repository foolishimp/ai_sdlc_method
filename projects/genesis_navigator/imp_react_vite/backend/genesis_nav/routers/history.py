"""Run history endpoints for Genesis Navigator.

Provides read-only access to the Genesis event stream as structured run history:
    GET /api/projects/{project_id}/runs           — list all runs (current + archived)
    GET /api/projects/{project_id}/runs/current   — live workspace as a run summary
    GET /api/projects/{project_id}/runs/{run_id}  — full event timeline for a run

All endpoints are read-only (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-HIST-001
# Implements: REQ-F-HIST-002
# Implements: REQ-F-HIST-003
# Implements: REQ-F-API-005
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


def _resolve_project(project_id: str) -> Path:
    """Resolve project_id to its filesystem path or raise 404."""
    from genesis_nav import main as _main
    from genesis_nav.scanner.workspace_scanner import get_project_path

    root = Path(_main.get_root_dir())
    path = get_project_path(root, project_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return path


@router.get("/api/projects/{project_id}/runs", tags=["history"])
def list_runs(project_id: str):
    """List all runs for a project.

    Returns the current live workspace run first, followed by archived e2e
    runs sorted newest-first.

    Args:
        project_id: Project identifier (from ``GET /api/projects``).

    Returns:
        List of :class:`~genesis_nav.models.schemas.RunSummary` objects.

    Raises:
        HTTPException: 404 if project not found.
    """
    from genesis_nav.models.schemas import RunSummary
    from genesis_nav.readers.run_reader import list_all_runs

    project_path = _resolve_project(project_id)
    return [RunSummary(**r) for r in list_all_runs(project_path)]


@router.get("/api/projects/{project_id}/runs/current", tags=["history"])
def get_current_run(project_id: str):
    """Return the live workspace as a run summary.

    Args:
        project_id: Project identifier.

    Returns:
        A :class:`~genesis_nav.models.schemas.RunSummary` with run_id='current'.

    Raises:
        HTTPException: 404 if project not found.
    """
    from genesis_nav.models.schemas import RunSummary
    from genesis_nav.readers.run_reader import read_current_run

    project_path = _resolve_project(project_id)
    return RunSummary(**read_current_run(project_path))


@router.get("/api/projects/{project_id}/runs/{run_id}", tags=["history"])
def get_run_timeline(project_id: str, run_id: str):
    """Return the full event timeline for a specific run.

    Events are grouped into segments by (feature, edge) in chronological order.

    Args:
        project_id: Project identifier.
        run_id: 'current' for the live workspace, or an archived run directory name.

    Returns:
        A :class:`~genesis_nav.models.schemas.RunTimeline` object.

    Raises:
        HTTPException: 404 if project or run not found.
    """
    from genesis_nav.models.schemas import RunTimeline
    from genesis_nav.readers.run_reader import read_run_timeline

    project_path = _resolve_project(project_id)
    timeline = read_run_timeline(project_path, run_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return RunTimeline(**timeline)
