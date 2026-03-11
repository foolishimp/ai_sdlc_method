"""FastAPI router for the /api/projects endpoint.

Returns a list of ProjectSummary objects by delegating to the workspace scanner.
"""

# Implements: REQ-F-API-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from genesis_nav.models.schemas import ProjectSummary
from genesis_nav.scanner.workspace_scanner import scan_workspace

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects", response_model=list[ProjectSummary])
def list_projects() -> list[ProjectSummary]:
    """Return all Genesis projects discovered under the configured root directory.

    Scans the root directory set at startup via :mod:`genesis_nav.main`
    ``_config["root_dir"]``. The scan is synchronous and runs in the request
    thread; at ≤200 projects it completes well within the 2-second budget
    (REQ-NFR-PERF-001).

    Returns:
        JSON array of :class:`~genesis_nav.models.schemas.ProjectSummary` objects.
    """
    import genesis_nav.main as _main  # late import avoids circular dependency

    root = Path(_main.get_root_dir())
    return scan_workspace(root)
