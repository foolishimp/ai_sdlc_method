"""Detail endpoint: GET /api/projects/{project_id}.

Returns full feature-level data for a single Genesis project identified by
``project_id``.  All data is derived by reading the workspace on-demand —
no caching, no writes (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-API-002
# Implements: REQ-F-STAT-001
# Implements: REQ-F-STAT-002
# Implements: REQ-F-STAT-003
# Implements: REQ-F-STAT-004
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/projects/{project_id}", tags=["projects"])
def get_project_detail(project_id: str):
    """Return full detail for a single Genesis project.

    Locates the project by scanning the configured workspace root, then reads
    all feature vectors and events to build a
    :class:`~genesis_nav.models.schemas.ProjectDetail` response.

    Args:
        project_id: The unique project identifier (as returned by
            ``GET /api/projects``).

    Returns:
        A :class:`~genesis_nav.models.schemas.ProjectDetail` dict.

    Raises:
        HTTPException: 404 if no project with ``project_id`` is found.
    """
    # Late imports to avoid circular dependency with main.py
    from genesis_nav import main as _main
    from genesis_nav.models.schemas import EdgeTrajectory, FeatureDetail, ProjectDetail
    from genesis_nav.readers.event_reader import read_events
    from genesis_nav.readers.feature_reader import read_features
    from genesis_nav.readers.state_computer import build_feature_detail, compute_project_state
    from genesis_nav.scanner.workspace_scanner import get_project_path

    root = Path(_main.get_root_dir())
    project_path = get_project_path(root, project_id)

    if project_path is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    events = read_events(project_path)
    raw_features = read_features(project_path)
    state = compute_project_state(raw_features)

    feature_details: list[FeatureDetail] = []
    for feat_dict in raw_features:
        detail_dict = build_feature_detail(feat_dict, events)
        trajectory = [EdgeTrajectory(**e) for e in detail_dict["trajectory"]]
        feature_details.append(
            FeatureDetail(
                feature_id=detail_dict["feature_id"],
                title=detail_dict["title"],
                status=detail_dict["status"],
                current_edge=detail_dict["current_edge"],
                delta=detail_dict["delta"],
                hamiltonian=detail_dict["hamiltonian"],
                trajectory=trajectory,
                error=detail_dict["error"],
            )
        )

    total_edges = sum(len(fd.trajectory) for fd in feature_details)
    converged_edges = sum(
        1 for fd in feature_details for edge in fd.trajectory if edge.status == "converged"
    )

    return ProjectDetail(
        project_id=project_id,
        name=project_path.name,
        state=state,
        features=feature_details,
        total_edges=total_edges,
        converged_edges=converged_edges,
    )
