"""Shared fixtures for genesis_nav test suite."""

from __future__ import annotations

import builtins
import json
from pathlib import Path
from typing import Callable

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_genesis_project(
    base: Path,
    name: str,
    events: list[dict] | None = None,
    active_features: list[str] | None = None,
    completed_features: list[str] | None = None,
) -> Path:
    """Create a minimal Genesis project dir under *base/name*.

    Args:
        base: Parent directory.
        name: Project directory name (may contain path separators for nesting).
        events: JSONL events to write to events.jsonl.  If None a single
            ``project_initialized`` event is used.
        active_features: Filenames (*.yml) to create in features/active/.
        completed_features: Filenames (*.yml) to create in features/completed/.

    Returns:
        Path to the created project directory.
    """
    project = base / name
    events_dir = project / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True)

    if events is None:
        events = [
            {
                "event_type": "project_initialized",
                "timestamp": "2026-01-01T00:00:00Z",
            }
        ]
    (events_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
    )

    if active_features:
        active_dir = project / ".ai-workspace" / "features" / "active"
        active_dir.mkdir(parents=True)
        for fname in active_features:
            (active_dir / fname).write_text("feature: stub\n")

    if completed_features:
        completed_dir = project / ".ai-workspace" / "features" / "completed"
        completed_dir.mkdir(parents=True)
        for fname in completed_features:
            (completed_dir / fname).write_text("feature: stub\n")

    return project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_workspace(
    tmp_path: Path,
) -> tuple[Path, Callable[..., Path]]:
    """Fixture that provides (root, make_project).

    ``make_project(name, events=None, active_features=None, completed_features=None)``
    creates a Genesis project directory under *root* and returns its path.
    """

    def make_project(
        name: str,
        events: list[dict] | None = None,
        active_features: list[str] | None = None,
        completed_features: list[str] | None = None,
    ) -> Path:
        return _make_genesis_project(
            tmp_path,
            name,
            events=events,
            active_features=active_features,
            completed_features=completed_features,
        )

    return tmp_path, make_project


@pytest.fixture
def assert_no_writes(monkeypatch: pytest.MonkeyPatch):
    """Monkeypatch builtins.open to capture write-mode calls.

    After the test body the fixture asserts that *no* write-mode opens occurred,
    verifying REQ-NFR-ARCH-002 (zero filesystem writes in API handlers).

    Yields the accumulated list of (file, mode) tuples so tests can inspect it.
    """
    writes: list[tuple[object, str]] = []
    _real_open = builtins.open

    def _patched_open(file, mode="r", *args, **kwargs):
        mode_str = str(mode)
        if any(c in mode_str for c in ("w", "a", "x")):
            writes.append((file, mode_str))
        return _real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _patched_open)
    yield writes
    assert writes == [], f"Unexpected filesystem writes detected: {writes}"
