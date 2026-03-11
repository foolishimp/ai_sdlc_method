"""Feature detail endpoint: GET /api/projects/{project_id}/features/{feature_id}.

Returns full spec data for a single feature vector: title, status, trajectory,
satisfies list, and acceptance criteria.  All data is derived by reading the
workspace on-demand — no caching, no writes (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-FEATDETAIL-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


def _extract_acceptance_criteria(feature_dict: dict) -> list[str]:
    """Extract acceptance criteria from the feature vector's constraints block."""
    constraints = feature_dict.get("constraints")
    if isinstance(constraints, dict):
        result = constraints.get("acceptance_criteria")
        if isinstance(result, list):
            return [str(c) for c in result]
    return []


@router.get("/api/projects/{project_id}/features/{feature_id}", tags=["features"])
def get_feature_detail(project_id: str, feature_id: str):
    """Return full spec detail for a single feature vector.

    Locates the feature by scanning active and completed feature directories,
    combines the YAML spec data with event-derived trajectory and Hamiltonian.

    Args:
        project_id: Project identifier (from ``GET /api/projects``).
        feature_id: Feature identifier (e.g. ``REQ-F-AUTH-001``).

    Returns:
        A :class:`~genesis_nav.models.schemas.FeatureDetail` dict including
        ``satisfies`` and ``acceptance_criteria`` fields.

    Raises:
        HTTPException: 404 if project or feature not found.
    """
    from genesis_nav import main as _main
    from genesis_nav.models.schemas import EdgeTrajectory, FeatureDetail
    from genesis_nav.readers.event_reader import read_events
    from genesis_nav.readers.feature_reader import read_features
    from genesis_nav.readers.state_computer import build_feature_detail
    from genesis_nav.scanner.workspace_scanner import get_project_path

    root = Path(_main.get_root_dir())
    project_path = get_project_path(root, project_id)

    if project_path is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    events = read_events(project_path)
    raw_features = read_features(project_path)

    feature_dict = next(
        (f for f in raw_features if f.get("feature_id") == feature_id),
        None,
    )
    if feature_dict is None:
        raise HTTPException(
            status_code=404,
            detail=f"Feature '{feature_id}' not found in project '{project_id}'.",
        )

    detail_dict = build_feature_detail(feature_dict, events)
    trajectory = [EdgeTrajectory(**e) for e in detail_dict["trajectory"]]

    return FeatureDetail(
        feature_id=detail_dict["feature_id"],
        title=detail_dict["title"],
        status=detail_dict["status"],
        current_edge=detail_dict["current_edge"],
        delta=detail_dict["delta"],
        hamiltonian=detail_dict["hamiltonian"],
        trajectory=trajectory,
        error=detail_dict["error"],
        satisfies=feature_dict.get("satisfies") or [],
        acceptance_criteria=_extract_acceptance_criteria(feature_dict),
    )
