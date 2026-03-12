# Implements: REQ-F-WATCH-001, REQ-F-WATCH-002
"""Watchdog-based filesystem observer with debouncing and periodic discovery.

Watches the root watch_dirs (one FSEvent stream per root) rather than one
stream per project. This avoids hitting macOS's FSEvent stream limit when
many archived e2e run directories are visible to the scanner.

A periodic rescan discovers new projects that appear after startup.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from genesis_monitor.scanner import PRUNE_DIRS, scan_roots

if TYPE_CHECKING:
    from genesis_monitor.registry import ProjectRegistry
    from genesis_monitor.server.broadcaster import SSEBroadcaster

logger = logging.getLogger(__name__)

RESCAN_INTERVAL_S = 30

# Path components that indicate noisy, non-workspace file changes.
# Changes inside these directories do not carry methodology signal and
# would continuously reset the debounce timer (e.g. Vite HMR, pytest cache).
_NOISY_DIRS = PRUNE_DIRS | {".vite", "dist", "build", ".pytest_cache"}


class _RootHandler(FileSystemEventHandler):
    """Handles events from a root watch directory.

    Routes each filesystem event to the affected project (if any) and
    debounces refreshes per project to avoid redundant work.
    """

    def __init__(
        self,
        registry: ProjectRegistry,
        broadcaster: SSEBroadcaster,
        debounce_ms: int,
    ) -> None:
        self._registry = registry
        self._broadcaster = broadcaster
        self._debounce_s = debounce_ms / 1000.0
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        affected_path = Path(event.src_path)
        # Skip events from noisy directories (node_modules, .vite, dist, etc.)
        # to prevent continuous debounce resets from dev tooling (Vite HMR, esbuild).
        if any(part in _NOISY_DIRS for part in affected_path.parts):
            return
        project_id = self._find_project(affected_path)
        if project_id is None:
            return
        with self._lock:
            existing = self._timers.get(project_id)
            if existing:
                existing.cancel()
            timer = threading.Timer(self._debounce_s, self._fire_refresh, [project_id])
            timer.daemon = True
            timer.start()
            self._timers[project_id] = timer

    def _find_project(self, changed_path: Path) -> str | None:
        """Return the project_id whose path contains changed_path, or None."""
        for project in self._registry.list_projects():
            try:
                changed_path.relative_to(project.path)
                return project.project_id
            except ValueError:
                continue
        return None

    def _fire_refresh(self, project_id: str) -> None:
        logger.info("Refreshing project: %s", project_id)
        self._registry.refresh_project(project_id)
        self._broadcaster.send("project_updated", {"project_id": project_id})
        with self._lock:
            self._timers.pop(project_id, None)


class WorkspaceWatcher:
    """Watches root directories for workspace changes.

    Two mechanisms:
    1. One watchdog observer per root watch_dir (not per project) — avoids
       hitting the macOS FSEvent stream limit when many projects are scanned.
    2. Periodic rescan of roots to discover new projects (every 30s).
    """

    def __init__(
        self,
        registry: ProjectRegistry,
        broadcaster: SSEBroadcaster,
        debounce_ms: int = 500,
    ) -> None:
        self._registry = registry
        self._broadcaster = broadcaster
        self._debounce_ms = debounce_ms
        self._observer = Observer()
        self._roots: list[Path] = []
        self._known_paths: set[Path] = set()
        self._rescan_timer: threading.Timer | None = None
        self._stopped = False

    def start(self, roots: list[Path]) -> None:
        """Start watching root dirs and periodic rescan."""
        self._roots = [r.expanduser().resolve() for r in roots]

        # Record all currently known projects (for rescan diff)
        for project in self._registry.list_projects():
            self._known_paths.add(project.path)

        # One handler + schedule per root — O(roots) FSEvent streams, not O(projects)
        handler = _RootHandler(self._registry, self._broadcaster, self._debounce_ms)
        for root in self._roots:
            if root.is_dir():
                self._observer.schedule(handler, str(root), recursive=True)
                logger.info("Watching root: %s", root)

        self._observer.start()
        self._schedule_rescan()

    def stop(self) -> None:
        """Stop the watcher and rescan timer."""
        self._stopped = True
        if self._rescan_timer:
            self._rescan_timer.cancel()
        self._observer.stop()
        self._observer.join(timeout=5)

    def _schedule_rescan(self) -> None:
        """Schedule the next periodic rescan."""
        if self._stopped:
            return
        self._rescan_timer = threading.Timer(RESCAN_INTERVAL_S, self._rescan)
        self._rescan_timer.daemon = True
        self._rescan_timer.start()

    def _rescan(self) -> None:
        """Rescan roots for new projects."""
        if self._stopped:
            return

        try:
            all_paths = scan_roots(self._roots)
            new_paths = [p for p in all_paths if p not in self._known_paths]

            for path in new_paths:
                project = self._registry.add_project(path)
                self._known_paths.add(path)
                self._broadcaster.send("project_added", {
                    "project_id": project.project_id,
                })
                logger.info("Discovered new project: %s (%s)", project.name, path)
        except Exception:
            logger.exception("Error during periodic rescan")

        self._schedule_rescan()
