"""Reader for Genesis workspace event streams.

Reads ``events.jsonl`` from a workspace, skipping malformed lines silently.
All operations are read-only (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-STAT-002
# Implements: REQ-F-STAT-004
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

import json
from pathlib import Path

_AI_WORKSPACE = ".ai-workspace"
_EVENTS_REL = f"{_AI_WORKSPACE}/events/events.jsonl"


def read_events(workspace_path: Path) -> list[dict]:
    """Read all events from the workspace event log.

    Reads ``.ai-workspace/events/events.jsonl`` and returns every valid JSON
    object as a dict.  Malformed lines are silently skipped.

    Args:
        workspace_path: Absolute path to the Genesis project root.

    Returns:
        List of parsed event dicts in file order.  Empty list if the file
        does not exist or cannot be read.
    """
    events_file = workspace_path / _EVENTS_REL
    if not events_file.is_file():
        return []

    events: list[dict] = []
    try:
        with events_file.open(encoding="utf-8") as fh:
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


def last_event_timestamp(events: list[dict]) -> str | None:
    """Return the ISO 8601 timestamp of the last event that carries one.

    Iterates the event list in reverse and returns the first ``timestamp``
    field found.

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
