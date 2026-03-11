"""Gap Analysis endpoint: GET /api/projects/{project_id}/gaps.

Returns a three-layer traceability gap report for a single Genesis project.
All data is derived on-demand — no caching, no writes (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-API-003
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/projects/{project_id}/gaps", tags=["gaps"])
def get_project_gaps(project_id: str):
    """Return the three-layer gap analysis report for a Genesis project.

    Scans the project for ``specification/requirements/REQUIREMENTS.md`` to
    collect the authoritative REQ key set, then compares against code
    annotations (``# Implements:``), test annotations (``# Validates:``),
    and telemetry annotations (``req="..."``).

    Args:
        project_id: The unique project identifier (as returned by
            ``GET /api/projects``).

    Returns:
        A :class:`~genesis_nav.models.schemas.GapReport` dict.

    Raises:
        HTTPException: 404 if no project with ``project_id`` is found.
    """
    from genesis_nav import main as _main
    from genesis_nav.analyzers.gap_analyzer import analyze_gaps
    from genesis_nav.models.schemas import GapItem, GapLayer, GapReport
    from genesis_nav.scanner.workspace_scanner import get_project_path

    root = Path(_main.get_root_dir())
    project_path = get_project_path(root, project_id)

    if project_path is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    raw = analyze_gaps(project_path)
    raw["project_id"] = project_id

    def _make_layer(layer_dict: dict) -> GapLayer:
        return GapLayer(
            gap_count=layer_dict["gap_count"],
            coverage_pct=layer_dict["coverage_pct"],
            gaps=[GapItem(**g) for g in layer_dict["gaps"]],
        )

    return GapReport(
        project_id=raw["project_id"],
        computed_at=raw["computed_at"],
        health_signal=raw["health_signal"],
        layer_1=_make_layer(raw["layer_1"]),
        layer_2=_make_layer(raw["layer_2"]),
        layer_3=_make_layer(raw["layer_3"]),
    )
