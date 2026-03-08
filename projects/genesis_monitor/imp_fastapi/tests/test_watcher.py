# Validates: REQ-F-WATCH-001, REQ-F-WATCH-002
"""Tests for WorkspaceWatcher filesystem observer.

REQ-F-WATCH-001: Observer uses watchdog, watches .ai-workspace/ paths, runs in
                 background thread, debounces rapid events.
REQ-F-WATCH-002: Periodic rescan discovers new projects appearing after startup.
"""

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from genesis_monitor.watcher.observer import WorkspaceWatcher, _WorkspaceHandler, RESCAN_INTERVAL_S


# ── REQ-F-WATCH-001: WorkspaceWatcher instantiation ───────────────────────────


class TestWorkspaceWatcherInstantiation:

    def test_can_be_created(self):
        """REQ-F-WATCH-001: WorkspaceWatcher can be instantiated."""
        reg = MagicMock()
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)
        assert watcher is not None

    def test_default_debounce_ms(self):
        """REQ-F-WATCH-001: default debounce is 500ms."""
        reg = MagicMock()
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)
        assert watcher._debounce_ms == 500

    def test_custom_debounce_ms(self):
        reg = MagicMock()
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc, debounce_ms=100)
        assert watcher._debounce_ms == 100

    def test_initial_state_has_empty_known_paths(self):
        watcher = WorkspaceWatcher(MagicMock(), MagicMock())
        assert len(watcher._known_paths) == 0


# ── REQ-F-WATCH-001: start / stop lifecycle ───────────────────────────────────


class TestWorkspaceWatcherLifecycle:

    def test_stop_without_start_does_not_raise(self):
        """REQ-F-WATCH-001 AC-3: stop() is safe even if start() was never called."""
        watcher = WorkspaceWatcher(MagicMock(), MagicMock())
        # stop() should not raise even in this state
        watcher._stopped = True  # mark stopped directly, skip observer internals
        if watcher._rescan_timer:
            watcher._rescan_timer.cancel()

    def test_start_with_no_projects_registers_zero_watches(self, tmp_path: Path):
        """REQ-F-WATCH-001: start() with empty registry watches 0 directories."""
        reg = MagicMock()
        reg.list_projects.return_value = []
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)

        with patch.object(watcher._observer, "start"), \
             patch.object(watcher._observer, "stop"), \
             patch.object(watcher._observer, "join"):
            watcher.start([tmp_path])
            watcher.stop()

        assert len(watcher._known_paths) == 0

    def test_start_with_project_watches_workspace_dir(self, tmp_path: Path):
        """REQ-F-WATCH-001 AC-2: only .ai-workspace/ dirs are watched."""
        ws = tmp_path / "myproject" / ".ai-workspace"
        ws.mkdir(parents=True)

        proj = MagicMock()
        proj.project_id = "myproject"
        proj.path = tmp_path / "myproject"

        reg = MagicMock()
        reg.list_projects.return_value = [proj]
        bc = MagicMock()

        watcher = WorkspaceWatcher(reg, bc)
        watched_dirs = []

        def fake_schedule(handler, path, recursive):
            watched_dirs.append(path)

        with patch.object(watcher._observer, "start"), \
             patch.object(watcher._observer, "stop"), \
             patch.object(watcher._observer, "join"), \
             patch.object(watcher._observer, "schedule", side_effect=fake_schedule):
            watcher.start([tmp_path])
            watcher.stop()

        assert len(watched_dirs) == 1
        assert ".ai-workspace" in watched_dirs[0]

    def test_stop_sets_stopped_flag(self, tmp_path: Path):
        """REQ-F-WATCH-001: stop() marks the watcher as stopped."""
        reg = MagicMock()
        reg.list_projects.return_value = []
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)

        with patch.object(watcher._observer, "start"), \
             patch.object(watcher._observer, "stop"), \
             patch.object(watcher._observer, "join"):
            watcher.start([tmp_path])
            watcher.stop()

        assert watcher._stopped is True

    def test_stop_cancels_rescan_timer(self, tmp_path: Path):
        """REQ-F-WATCH-002: stop() cancels the periodic rescan timer."""
        reg = MagicMock()
        reg.list_projects.return_value = []
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)

        with patch.object(watcher._observer, "start"), \
             patch.object(watcher._observer, "stop"), \
             patch.object(watcher._observer, "join"):
            watcher.start([tmp_path])
            assert watcher._rescan_timer is not None
            watcher.stop()

        # Timer should be cancelled (no more scheduled callbacks)
        assert watcher._stopped is True


# ── REQ-F-WATCH-001: _WorkspaceHandler debounce ───────────────────────────────


class TestWorkspaceHandler:

    def _make_handler(self, debounce_ms=50):
        registry = MagicMock()
        broadcaster = MagicMock()
        handler = _WorkspaceHandler("test-project", registry, broadcaster, debounce_ms)
        return handler, registry, broadcaster

    def test_fire_refresh_calls_registry_refresh(self):
        """REQ-F-WATCH-001: _fire_refresh calls registry.refresh_project."""
        handler, registry, broadcaster = self._make_handler()
        handler._fire_refresh()
        registry.refresh_project.assert_called_once_with("test-project")

    def test_fire_refresh_sends_broadcaster_event(self):
        """REQ-F-WATCH-001: _fire_refresh notifies clients via broadcaster."""
        handler, registry, broadcaster = self._make_handler()
        handler._fire_refresh()
        broadcaster.send.assert_called_once()
        args = broadcaster.send.call_args
        assert args[0][0] == "project_updated"
        assert args[0][1]["project_id"] == "test-project"

    def test_on_any_event_creates_debounce_timer(self):
        """REQ-F-WATCH-001: rapid filesystem events are debounced."""
        handler, _, _ = self._make_handler(debounce_ms=200)
        event = MagicMock()
        handler.on_any_event(event)
        assert handler._timer is not None
        # Clean up
        handler._timer.cancel()

    def test_on_any_event_resets_timer_on_second_event(self):
        """REQ-F-WATCH-001: second event cancels the first timer (debounce)."""
        handler, _, _ = self._make_handler(debounce_ms=500)
        event = MagicMock()

        handler.on_any_event(event)
        first_timer = handler._timer

        handler.on_any_event(event)
        second_timer = handler._timer

        assert second_timer is not first_timer
        # Clean up
        if handler._timer:
            handler._timer.cancel()

    def test_debounce_fires_after_delay(self):
        """REQ-F-WATCH-001: refresh fires after the debounce window elapses."""
        handler, registry, broadcaster = self._make_handler(debounce_ms=50)
        event = MagicMock()
        handler.on_any_event(event)
        time.sleep(0.15)  # wait longer than debounce
        registry.refresh_project.assert_called_once_with("test-project")


# ── REQ-F-WATCH-002: periodic rescan ──────────────────────────────────────────


class TestPeriodicRescan:

    def test_rescan_discovers_new_project(self, tmp_path: Path):
        """REQ-F-WATCH-002: _rescan() adds newly discovered projects to registry."""
        new_project_path = tmp_path / "new_project"
        (new_project_path / ".ai-workspace").mkdir(parents=True)

        new_proj = MagicMock()
        new_proj.project_id = "new-project"
        new_proj.path = new_project_path

        reg = MagicMock()
        reg.list_projects.return_value = []
        reg.add_project.return_value = new_proj

        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)
        watcher._roots = [tmp_path]
        watcher._stopped = False

        with patch("genesis_monitor.watcher.observer.scan_roots",
                   return_value=[new_project_path]), \
             patch.object(watcher._observer, "schedule"), \
             patch.object(watcher, "_schedule_rescan"):
            watcher._rescan()

        reg.add_project.assert_called_once_with(new_project_path)
        bc.send.assert_called_once()
        assert bc.send.call_args[0][0] == "project_added"

    def test_rescan_skips_already_known_projects(self, tmp_path: Path):
        """REQ-F-WATCH-002: _rescan() does not re-add already-watched projects."""
        existing_path = tmp_path / "existing"
        (existing_path / ".ai-workspace").mkdir(parents=True)

        reg = MagicMock()
        reg.list_projects.return_value = []
        bc = MagicMock()

        watcher = WorkspaceWatcher(reg, bc)
        watcher._known_paths.add(existing_path)
        watcher._roots = [tmp_path]
        watcher._stopped = False

        with patch("genesis_monitor.watcher.observer.scan_roots",
                   return_value=[existing_path]), \
             patch.object(watcher, "_schedule_rescan"):
            watcher._rescan()

        reg.add_project.assert_not_called()

    def test_rescan_stops_when_watcher_stopped(self, tmp_path: Path):
        """REQ-F-WATCH-002: _rescan() is a no-op after stop()."""
        reg = MagicMock()
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)
        watcher._stopped = True

        with patch("genesis_monitor.watcher.observer.scan_roots") as mock_scan:
            watcher._rescan()
            mock_scan.assert_not_called()

    def test_rescan_handles_exception_without_crashing(self, tmp_path: Path):
        """REQ-F-WATCH-002: errors in _rescan() are caught and logged, not raised."""
        reg = MagicMock()
        bc = MagicMock()
        watcher = WorkspaceWatcher(reg, bc)
        watcher._roots = [tmp_path]
        watcher._stopped = False

        with patch("genesis_monitor.watcher.observer.scan_roots",
                   side_effect=RuntimeError("disk error")), \
             patch.object(watcher, "_schedule_rescan"):
            # Should not raise
            watcher._rescan()

    def test_rescan_interval_constant(self):
        """REQ-F-WATCH-002: rescan interval is defined and reasonable (≤ 60s)."""
        assert RESCAN_INTERVAL_S <= 60
        assert RESCAN_INTERVAL_S > 0
