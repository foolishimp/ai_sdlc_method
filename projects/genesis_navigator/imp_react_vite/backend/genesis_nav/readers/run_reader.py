"""Reader for Genesis run history.

A "run" is a distinct events.jsonl snapshot — either the live workspace
(run_id='current') or an archived e2e run directory discovered under
``tests/e2e/runs/e2e_*/``.

All operations are read-only (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-HIST-001
# Implements: REQ-F-HIST-002
# Implements: REQ-F-HIST-003
# Implements: REQ-F-API-005
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_WORKSPACE_EVENTS = ".ai-workspace/events/events.jsonl"
_E2E_RUNS_GLOB = "tests/e2e/runs/e2e_*"


def _read_events_file(events_path: Path) -> list[dict]:
    """Read and parse a JSONL events file, skipping malformed lines.

    Args:
        events_path: Path to the events.jsonl file.

    Returns:
        List of parsed event dicts in file order. Empty list if missing.
    """
    if not events_path.is_file():
        return []
    events: list[dict] = []
    try:
        with events_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        events.append(obj)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return []
    return events


def _compute_run_summary(events: list[dict], run_id: str, *, is_current: bool) -> dict:
    """Compute a run summary dict from a list of parsed events.

    Args:
        events: All parsed event dicts from the run.
        run_id: Identifier for this run.
        is_current: Whether this is the live workspace run.

    Returns:
        Dict matching the RunSummary schema.
    """
    # First timestamp from any event (SDLC or OpenLineage)
    timestamp: Optional[str] = None
    for e in events:
        ts = e.get("timestamp") or e.get("eventTime")
        if ts and isinstance(ts, str):
            timestamp = ts
            break

    # Count unique feature+edge pairs from edge_converged events
    sdlc = [e for e in events if "event_type" in e]
    converged_pairs: set[tuple[str, str]] = {
        (e.get("feature", ""), e.get("edge", ""))
        for e in sdlc
        if e.get("event_type") == "edge_converged"
    }
    edges_traversed = len(converged_pairs)

    # Determine final state from event stream
    converged_features: set[str] = set()
    iterating_features: set[str] = set()
    for e in sdlc:
        feat = e.get("feature")
        if not feat:
            continue
        etype = e.get("event_type", "")
        if etype == "edge_converged":
            converged_features.add(feat)
        elif etype in ("edge_started", "iteration_completed"):
            iterating_features.add(feat)

    still_iterating = iterating_features - converged_features
    if still_iterating:
        final_state = "ITERATING"
    elif converged_features:
        final_state = "CONVERGED"
    else:
        final_state = "UNINITIALIZED"

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "event_count": len(events),
        "edges_traversed": edges_traversed,
        "final_state": final_state,
        "is_current": is_current,
    }


def read_current_run(project_path: Path) -> dict:
    """Read the live workspace events as the 'current' run summary.

    Args:
        project_path: Absolute path to the Genesis project root.

    Returns:
        Dict matching RunSummary schema with run_id='current'.
    """
    events_path = project_path / _WORKSPACE_EVENTS
    events = _read_events_file(events_path)
    return _compute_run_summary(events, "current", is_current=True)


def list_archived_runs(project_path: Path) -> list[dict]:
    """Discover archived e2e run directories and return their summaries.

    Scans ``tests/e2e/runs/e2e_*/events.jsonl`` under the project root.
    Results are sorted newest-first by directory name (which is timestamped).

    Args:
        project_path: Absolute path to the Genesis project root.

    Returns:
        List of RunSummary dicts, newest first. Empty if none found.
    """
    runs: list[dict] = []
    for run_dir in sorted(project_path.glob(_E2E_RUNS_GLOB), reverse=True):
        if not run_dir.is_dir():
            continue
        events_path = run_dir / "events.jsonl"
        if not events_path.is_file():
            events_path = run_dir / ".ai-workspace" / "events" / "events.jsonl"
        if not events_path.is_file():
            continue
        events = _read_events_file(events_path)
        runs.append(_compute_run_summary(events, run_dir.name, is_current=False))
    return runs


def list_all_runs(project_path: Path) -> list[dict]:
    """Return all runs: current first, then archived newest-first.

    Args:
        project_path: Absolute path to the Genesis project root.

    Returns:
        List of RunSummary dicts starting with the live workspace run.
    """
    current = read_current_run(project_path)
    archived = list_archived_runs(project_path)
    return [current] + archived


def _build_timeline_segments(events: list[dict]) -> list[dict]:
    """Group events into segments by (feature, edge) in chronological order.

    Each time the (feature, edge) pair changes a new segment is started.
    Events that share no feature/edge (project-level events) form their own
    segment with feature=None, edge=None.

    Args:
        events: All parsed event dicts in file order.

    Returns:
        List of segment dicts each with feature, edge, and events fields.
    """
    segments: list[dict] = []
    current_key: tuple[Optional[str], Optional[str]] = (None, None)
    current_events: list[dict] = []

    def _flush() -> None:
        if current_events:
            f, e = current_key
            segments.append({"feature": f, "edge": e, "events": list(current_events)})

    for raw in events:
        feature = raw.get("feature") or None
        edge = raw.get("edge") or None
        key: tuple[Optional[str], Optional[str]] = (feature, edge)
        if key != current_key:
            _flush()
            current_key = key
            current_events = []
        current_events.append({
            "event_type": raw.get("event_type") or raw.get("eventType", "unknown"),
            "timestamp": raw.get("timestamp") or raw.get("eventTime"),
            "feature": feature,
            "edge": edge,
            "data": {
                k: v for k, v in raw.items()
                if k not in ("event_type", "eventType", "timestamp", "eventTime", "feature", "edge")
            },
        })

    _flush()
    return segments


def read_run_timeline(project_path: Path, run_id: str) -> Optional[dict]:
    """Return the full event timeline for a run, grouped by feature+edge.

    Args:
        project_path: Absolute path to the Genesis project root.
        run_id: 'current' for live workspace; directory name for archived runs.

    Returns:
        Dict matching RunTimeline schema, or None if run_id not found.
    """
    if run_id == "current":
        events_path = project_path / _WORKSPACE_EVENTS
        events = _read_events_file(events_path)
    else:
        run_dir: Optional[Path] = None
        for candidate in project_path.glob(_E2E_RUNS_GLOB):
            if candidate.name == run_id:
                run_dir = candidate
                break
        if run_dir is None:
            return None
        events_path = run_dir / "events.jsonl"
        if not events_path.is_file():
            events_path = run_dir / ".ai-workspace" / "events" / "events.jsonl"
        if not events_path.is_file():
            return None
        events = _read_events_file(events_path)

    return {
        "run_id": run_id,
        "event_count": len(events),
        "segments": _build_timeline_segments(events),
    }
