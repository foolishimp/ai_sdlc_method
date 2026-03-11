"""Recursive workspace scanner that discovers Genesis projects under a root directory.

A directory is a Genesis project if it contains ``.ai-workspace/events/events.jsonl``.
A directory that has ``.ai-workspace/`` but no ``events.jsonl`` is reported as
``uninitialized``.

Pruned directories (never descended into): ``.git``, ``node_modules``,
``__pycache__``, ``.venv``.
"""

# Implements: REQ-F-NAV-001
# Implements: REQ-BR-001
# Implements: REQ-BR-002
# Implements: REQ-NFR-PERF-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from genesis_nav.models.schemas import ProjectState, ProjectSummary
from genesis_nav.scanner.project_identity import derive_project_id

_PRUNE_DIRS: frozenset[str] = frozenset({".git", "node_modules", "__pycache__", ".venv"})
_AI_WORKSPACE = ".ai-workspace"
_EVENTS_JSONL = "events.jsonl"
_EVENTS_REL = os.path.join(_AI_WORKSPACE, "events", _EVENTS_JSONL)
_ACTIVE_FEATURES_REL = os.path.join(_AI_WORKSPACE, "features", "active")
_COMPLETED_FEATURES_REL = os.path.join(_AI_WORKSPACE, "features", "completed")

# Number of tail events to inspect for state computation
_STATE_WINDOW = 50
# Approximate max bytes to read from the tail of events.jsonl for state window
_TAIL_READ_BYTES = 32_768  # 32 KiB — plenty for 50 JSON lines


def scan_workspace(root: Path) -> list[ProjectSummary]:
    """Scan *root* recursively and return one ProjectSummary per Genesis project.

    Uses ``os.scandir()`` with early prune for performance (REQ-NFR-PERF-001).
    Never writes to any discovered workspace (REQ-NFR-ARCH-002).

    Args:
        root: Absolute path to the directory to scan.

    Returns:
        List of :class:`~genesis_nav.models.schemas.ProjectSummary` objects,
        one per discovered Genesis project.
    """
    root = root.resolve()
    results: list[ProjectSummary] = []
    seen_names: set[str] = set()
    _walk(root, root, results, seen_names)
    return results


def _walk(
    current: Path,
    root: Path,
    results: list[ProjectSummary],
    seen_names: set[str],
) -> None:
    """Recursively walk *current*, appending discovered projects to *results*.

    Args:
        current: Directory being scanned in this call.
        root: Top-level root of the scan (for relative-path id derivation).
        results: Accumulator for discovered :class:`ProjectSummary` objects.
        seen_names: Mutable set of project_ids already assigned; updated in-place.
    """
    try:
        entries = list(os.scandir(current))
    except PermissionError:
        return

    has_ai_workspace = False
    subdirs: list[Path] = []

    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            if entry.name in _PRUNE_DIRS:
                continue
            if entry.name == _AI_WORKSPACE:
                has_ai_workspace = True
            else:
                subdirs.append(Path(entry.path))

    if has_ai_workspace:
        t0 = time.perf_counter()
        summary = _build_summary(current, root, seen_names)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        summary = summary.model_copy(update={"scan_duration_ms": elapsed_ms})
        results.append(summary)
        # Do NOT descend into subdirs of a Genesis project — each project is atomic
        return

    for subdir in subdirs:
        _walk(subdir, root, results, seen_names)


def _build_summary(project_path: Path, root: Path, seen_names: set[str]) -> ProjectSummary:
    """Construct a ProjectSummary for a directory that contains .ai-workspace/.

    Args:
        project_path: Path to the project root directory.
        root: Scan root (for project_id disambiguation).
        seen_names: Mutable set tracking assigned project_ids.

    Returns:
        A :class:`~genesis_nav.models.schemas.ProjectSummary` describing the project.
    """
    events_jsonl = project_path / _EVENTS_REL

    if not events_jsonl.exists():
        return ProjectSummary(
            project_id=derive_project_id(project_path, root, seen_names),
            name=project_path.name,
            path=str(project_path),
            state=ProjectState.UNINITIALIZED,
            active_feature_count=0,
            converged_feature_count=0,
            last_event_at=None,
            scan_duration_ms=0.0,
        )

    tail_events = _read_tail_events(events_jsonl, _STATE_WINDOW)
    state = _compute_state(tail_events)
    last_event_at = _last_event_timestamp(tail_events)
    active_count = _count_yaml_files(project_path / _ACTIVE_FEATURES_REL)
    converged_count = _count_yaml_files(project_path / _COMPLETED_FEATURES_REL)
    project_id = derive_project_id(project_path, root, seen_names)

    return ProjectSummary(
        project_id=project_id,
        name=project_path.name,
        path=str(project_path),
        state=state,
        active_feature_count=active_count,
        converged_feature_count=converged_count,
        last_event_at=last_event_at,
        scan_duration_ms=0.0,  # patched by caller after timing
    )


def _read_tail_events(events_jsonl: Path, n: int) -> list[dict]:
    """Read up to the last *n* valid JSON lines from *events_jsonl*.

    Reads from the tail of the file for performance (REQ-NFR-PERF-001).
    Malformed lines are silently skipped.

    Args:
        events_jsonl: Path to ``events.jsonl``.
        n: Maximum number of events to return (from the tail).

    Returns:
        List of parsed event dicts, up to *n* entries, in file order.
    """
    try:
        size = events_jsonl.stat().st_size
    except OSError:
        return []

    read_offset = max(0, size - _TAIL_READ_BYTES)
    try:
        with events_jsonl.open("rb") as fh:
            fh.seek(read_offset)
            raw = fh.read()
    except OSError:
        return []

    lines = raw.splitlines()
    # If we sought mid-file the first partial line should be discarded
    if read_offset > 0 and lines:
        lines = lines[1:]

    events: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                events.append(obj)
        except (json.JSONDecodeError, ValueError):
            continue

    return events[-n:]


def _compute_state(events: list[dict]) -> ProjectState:
    """Derive a best-effort :class:`ProjectState` from a tail window of events.

    Rules (REQ-BR-002 — state derived from events only):
    - No events → UNINITIALIZED (caller ensures file exists so we use QUIESCENT)
    - Any ``iteration_completed`` with ``status: iterating`` → ITERATING
    - Last event is ``edge_converged`` → CONVERGED
    - Otherwise → QUIESCENT

    Args:
        events: Tail window of parsed event dicts from ``events.jsonl``.

    Returns:
        A :class:`~genesis_nav.models.schemas.ProjectState` value.
    """
    if not events:
        return ProjectState.QUIESCENT

    for ev in reversed(events):
        ev_type = ev.get("event_type", "") or ev.get("type", "")
        if ev_type == "iteration_completed" and ev.get("status") == "iterating":
            return ProjectState.ITERATING

    last = events[-1]
    last_type = last.get("event_type", "") or last.get("type", "")
    if last_type == "edge_converged":
        return ProjectState.CONVERGED

    return ProjectState.QUIESCENT


def _last_event_timestamp(events: list[dict]) -> Optional[str]:
    """Return the ISO 8601 timestamp of the last event that carries one.

    Args:
        events: Parsed event dicts, in file order.

    Returns:
        Timestamp string, or ``None`` if no event has a ``timestamp`` field.
    """
    for ev in reversed(events):
        ts = ev.get("timestamp")
        if ts and isinstance(ts, str):
            return ts
    return None


def _count_yaml_files(directory: Path) -> int:
    """Count ``.yml`` and ``.yaml`` files directly inside *directory*.

    Returns 0 if the directory does not exist.

    Args:
        directory: Path to inspect.

    Returns:
        Number of YAML files found (not recursive).
    """
    if not directory.is_dir():
        return 0
    count = 0
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith((".yml", ".yaml")):
                    count += 1
    except PermissionError:
        pass
    return count
