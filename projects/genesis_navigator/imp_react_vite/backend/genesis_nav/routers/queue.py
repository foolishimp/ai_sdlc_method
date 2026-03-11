"""Decision Queue endpoint: GET /api/projects/{project_id}/queue.

Returns a ranked list of actionable items for a Genesis project, ordered by
urgency (STUCK > BLOCKED > GAP_CLUSTER > IN_PROGRESS).
All data is derived on-demand — no caching, no writes (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-API-004
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/projects/{project_id}/queue", tags=["queue"])
def get_project_queue(project_id: str):
    """Return the ranked decision queue for a Genesis project.

    Combines feature vector status, event history, and gap analysis to surface
    the most urgent next action for the practitioner.

    Args:
        project_id: The unique project identifier (as returned by
            ``GET /api/projects``).

    Returns:
        List of :class:`~genesis_nav.models.schemas.QueueItem` dicts, sorted
        by urgency.  Returns a single "healthy" item when no issues are found.

    Raises:
        HTTPException: 404 if no project with ``project_id`` is found.
    """
    from genesis_nav import main as _main
    from genesis_nav.analyzers.gap_analyzer import analyze_gaps
    from genesis_nav.analyzers.queue_builder import build_queue_items
    from genesis_nav.models.schemas import QueueItem, QueueItemDetail
    from genesis_nav.readers.event_reader import read_events
    from genesis_nav.readers.feature_reader import read_features
    from genesis_nav.scanner.workspace_scanner import get_project_path

    root = Path(_main.get_root_dir())
    project_path = get_project_path(root, project_id)

    if project_path is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    features = read_features(project_path)
    events = read_events(project_path)
    gaps = analyze_gaps(project_path)

    raw_items = build_queue_items(features, events, gaps)

    return [
        QueueItem(
            type=item["type"],
            severity=item["severity"],
            feature_id=item.get("feature_id"),
            description=item["description"],
            command=item["command"],
            detail=QueueItemDetail(**item["detail"]),
        )
        for item in raw_items
    ]
