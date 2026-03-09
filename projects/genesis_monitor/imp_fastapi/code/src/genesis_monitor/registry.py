# Implements: REQ-F-DISC-002, REQ-F-CQRS-002
"""In-memory project registry — thread-safe store of discovered projects."""

import re
import threading
from datetime import datetime
from pathlib import Path

from genesis_monitor.models import Project
from genesis_monitor.scanner import build_workspace_hierarchy
from genesis_monitor.parsers import (
    detect_bootloader,
    parse_adrs,
    parse_constraints,
    parse_events,
    parse_feature_vectors,
    parse_graph_topology,
    parse_reviews,
    parse_status,
    parse_tasks,
)
from genesis_monitor.parsers.traceability import parse_traceability
from genesis_monitor.index import EventIndex


def _slugify(name: str) -> str:
    """Convert a directory name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


class ProjectRegistry:
    """Thread-safe registry of discovered AI SDLC projects."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._lock = threading.Lock()

    def add_project(self, path: Path) -> Project:
        """Add a project by its filesystem path. Parses all workspace data."""
        project_id = _slugify(path.name)
        workspace = path / ".ai-workspace"

        status = parse_status(workspace)
        # Prefer the name from STATUS.md heading (project_name field).
        # Fall back to directory name if STATUS.md is absent or generic.
        name = (status.project_name if status and status.project_name else None) or path.name

        events = parse_events(workspace, max_events=100000)
        project = Project(
            project_id=project_id,
            path=path,
            name=name,
            status=status,
            features=parse_feature_vectors(workspace, project_path=path),
            topology=parse_graph_topology(workspace, project_root=path),
            events=events,
            tasks=parse_tasks(workspace),
            constraints=parse_constraints(workspace),
            has_bootloader=detect_bootloader(path),
            last_updated=datetime.now(),
            traceability=parse_traceability(path),
            index=EventIndex.build(events),  # ADR-004: O(n) once at load
            adrs=parse_adrs(path),
            reviews=parse_reviews(workspace),
        )

        with self._lock:
            self._projects[project_id] = project

        return project

    def remove_project(self, path: Path) -> None:
        """Remove a project by path."""
        project_id = _slugify(path.name)
        with self._lock:
            self._projects.pop(project_id, None)

    def get_project(self, project_id: str) -> Project | None:
        """Get a project by its slug ID."""
        with self._lock:
            return self._projects.get(project_id)

    def list_projects(self) -> list[Project]:
        """List all registered projects, sorted by name."""
        with self._lock:
            return sorted(self._projects.values(), key=lambda p: p.name.lower())

    def refresh_project(self, project_id: str) -> Project | None:
        """Re-parse all data for an existing project."""
        with self._lock:
            existing = self._projects.get(project_id)

        if not existing:
            return None

        return self.add_project(existing.path)

    def project_id_for_path(self, path: Path) -> str | None:
        """Find the project_id that contains the given path."""
        with self._lock:
            for pid, proj in self._projects.items():
                try:
                    path.relative_to(proj.path)
                    return pid
                except ValueError:
                    continue
        return None

    def link_workspace_hierarchy(self) -> None:
        """Set parent_workspace_id and child_workspace_ids on all projects (GMON-005).

        A workspace B is a direct child of A if B.path is nested under A.path
        with no other registered project in between.  Calls build_workspace_hierarchy()
        from scanner.py and writes the relationships back into the in-memory projects.
        """
        with self._lock:
            projects = list(self._projects.values())

        if not projects:
            return

        paths = [p.path for p in projects]
        hierarchy = build_workspace_hierarchy(paths)  # parent_path → [child_path, ...]

        # Build a reverse lookup: path → project_id
        path_to_id: dict[Path, str] = {p.path.resolve(): p.project_id for p in projects}

        for project in projects:
            resolved = project.path.resolve()
            child_paths = hierarchy.get(resolved, [])
            child_ids = [path_to_id[cp] for cp in child_paths if cp in path_to_id]

            # Find the parent (a project whose children include this one)
            parent_id: str | None = None
            for candidate in projects:
                cres = candidate.path.resolve()
                if resolved in [cp for cp in hierarchy.get(cres, [])]:
                    parent_id = candidate.project_id
                    break

            with self._lock:
                pid = project.project_id
                if pid in self._projects:
                    self._projects[pid].child_workspace_ids = sorted(child_ids)
                    self._projects[pid].parent_workspace_id = parent_id
