# Validates: REQ-F-CQRS-001, REQ-F-CQRS-002, REQ-F-CQRS-003, REQ-F-CQRS-004
"""Tests for GMON-005: CQRS Workspace Hierarchy — scanner, registry, and route."""

from contextlib import asynccontextmanager
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from genesis_monitor.registry import ProjectRegistry
from genesis_monitor.scanner import build_workspace_hierarchy, scan_roots
from genesis_monitor.server.app import create_app
from genesis_monitor.server.broadcaster import SSEBroadcaster


# ── build_workspace_hierarchy ────────────────────────────────────────────────

class TestBuildWorkspaceHierarchy:
    """REQ-F-CQRS-001 / REQ-F-CQRS-002 — scanner hierarchy detection."""

    def test_flat_list_has_no_relationships(self, tmp_path: Path):
        """Independent sibling paths share no parent/child relationships."""
        a = tmp_path / "project_a"
        b = tmp_path / "project_b"
        a.mkdir()
        b.mkdir()
        result = build_workspace_hierarchy([a, b])
        assert result[a.resolve()] == []
        assert result[b.resolve()] == []

    def test_nested_path_is_child(self, tmp_path: Path):
        """B nested under A → A is parent, B is child."""
        parent = tmp_path / "parent"
        child = parent / "child_project"
        parent.mkdir()
        child.mkdir()
        result = build_workspace_hierarchy([parent, child])
        assert child.resolve() in result[parent.resolve()]
        assert result[child.resolve()] == []

    def test_direct_child_not_grandchild(self, tmp_path: Path):
        """With three levels, each path is a direct child of its immediate parent."""
        grandparent = tmp_path / "gp"
        parent = grandparent / "p"
        child = parent / "c"
        grandparent.mkdir()
        parent.mkdir()
        child.mkdir()
        result = build_workspace_hierarchy([grandparent, parent, child])
        # grandparent → parent (direct)
        assert parent.resolve() in result[grandparent.resolve()]
        assert child.resolve() not in result[grandparent.resolve()]
        # parent → child (direct)
        assert child.resolve() in result[parent.resolve()]

    def test_multiple_children(self, tmp_path: Path):
        """A parent may have multiple direct children."""
        parent = tmp_path / "parent"
        c1 = parent / "child1"
        c2 = parent / "child2"
        parent.mkdir()
        c1.mkdir()
        c2.mkdir()
        result = build_workspace_hierarchy([parent, c1, c2])
        children = result[parent.resolve()]
        assert c1.resolve() in children
        assert c2.resolve() in children
        assert len(children) == 2

    def test_empty_list(self):
        """Empty input returns empty dict."""
        result = build_workspace_hierarchy([])
        assert result == {}

    def test_single_path(self, tmp_path: Path):
        """Single path has no children."""
        p = tmp_path / "solo"
        p.mkdir()
        result = build_workspace_hierarchy([p])
        assert result[p.resolve()] == []


# ── ProjectRegistry.link_workspace_hierarchy ─────────────────────────────────

def _make_workspace(base: Path, name: str) -> Path:
    """Create a minimal .ai-workspace/ under base/name."""
    project_dir = base / name
    ws = project_dir / ".ai-workspace"
    ws.mkdir(parents=True)
    (ws / "STATUS.md").write_text(f"# {name}\n")
    events_dir = ws / "events"
    events_dir.mkdir()
    (events_dir / "events.jsonl").write_text("")
    return project_dir


class TestRegistryLinkHierarchy:
    """REQ-F-CQRS-002 — registry links parent/child IDs after project load."""

    def test_sibling_projects_have_no_parent(self, tmp_path: Path):
        reg = ProjectRegistry()
        a = _make_workspace(tmp_path, "project_a")
        b = _make_workspace(tmp_path, "project_b")
        reg.add_project(a)
        reg.add_project(b)
        reg.link_workspace_hierarchy()
        pa = reg.get_project("project-a")
        pb = reg.get_project("project-b")
        assert pa.parent_workspace_id is None
        assert pb.parent_workspace_id is None
        assert pa.child_workspace_ids == []
        assert pb.child_workspace_ids == []

    def test_parent_gets_child_id(self, tmp_path: Path):
        reg = ProjectRegistry()
        parent = _make_workspace(tmp_path, "parent_ws")
        child = _make_workspace(parent, "child_ws")
        reg.add_project(parent)
        reg.add_project(child)
        reg.link_workspace_hierarchy()
        p = reg.get_project("parent-ws")
        c = reg.get_project("child-ws")
        assert c.project_id in p.child_workspace_ids
        assert c.parent_workspace_id == p.project_id

    def test_child_has_no_extra_children(self, tmp_path: Path):
        reg = ProjectRegistry()
        parent = _make_workspace(tmp_path, "outer")
        child = _make_workspace(parent, "inner")
        reg.add_project(parent)
        reg.add_project(child)
        reg.link_workspace_hierarchy()
        c = reg.get_project("inner")
        assert c.child_workspace_ids == []

    def test_link_idempotent(self, tmp_path: Path):
        """Calling link_workspace_hierarchy twice does not duplicate IDs."""
        reg = ProjectRegistry()
        parent = _make_workspace(tmp_path, "p")
        child = _make_workspace(parent, "c")
        reg.add_project(parent)
        reg.add_project(child)
        reg.link_workspace_hierarchy()
        reg.link_workspace_hierarchy()
        p = reg.get_project("p")
        assert p.child_workspace_ids.count("c") == 1

    def test_empty_registry_no_error(self):
        reg = ProjectRegistry()
        reg.link_workspace_hierarchy()  # should not raise


# ── Workspace Hierarchy route ─────────────────────────────────────────────────

@pytest.fixture
def nested_client(tmp_path: Path):
    """TestClient with a parent project that has one child workspace."""
    parent_dir = tmp_path / "parent_project"
    child_dir = parent_dir / "child_project"
    # build workspaces
    for d in [parent_dir, child_dir]:
        ws = d / ".ai-workspace"
        ws.mkdir(parents=True)
        (ws / "STATUS.md").write_text(f"# {d.name}\n")
        (ws / "events").mkdir()
        (ws / "events" / "events.jsonl").write_text("")
        features = ws / "features" / "active"
        features.mkdir(parents=True)
        (features / "REQ-F-EXAMPLE-001.yml").write_text(yaml.dump({
            "feature": "REQ-F-EXAMPLE-001",
            "title": "Example feature",
            "status": "converged",
            "vector_type": "feature",
        }))

    reg = ProjectRegistry()
    reg.add_project(parent_dir)
    reg.add_project(child_dir)
    reg.link_workspace_hierarchy()
    bc = SSEBroadcaster()

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    app = create_app(
        watch_dirs=[tmp_path],
        _registry=reg,
        _broadcaster=bc,
        _lifespan=noop_lifespan,
    )
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client, reg


class TestWorkspaceHierarchyRoute:
    """REQ-F-CQRS-004 — workspace hierarchy fragment route."""

    def test_route_returns_200(self, nested_client):
        client, _ = nested_client
        resp = client.get("/fragments/project/parent-project/workspace-hierarchy")
        assert resp.status_code == 200

    def test_route_shows_child_link(self, nested_client):
        client, _ = nested_client
        resp = client.get("/fragments/project/parent-project/workspace-hierarchy")
        assert "child-project" in resp.text

    def test_route_shows_event_count(self, nested_client):
        client, _ = nested_client
        resp = client.get("/fragments/project/parent-project/workspace-hierarchy")
        # event count column present (even if 0)
        assert resp.status_code == 200
        assert "Events" in resp.text or "0" in resp.text

    def test_child_shows_parent_link(self, nested_client):
        client, _ = nested_client
        resp = client.get("/fragments/project/child-project/workspace-hierarchy")
        assert resp.status_code == 200
        assert "parent-project" in resp.text

    def test_unknown_project_returns_empty(self, nested_client):
        client, _ = nested_client
        resp = client.get("/fragments/project/nonexistent-xyz/workspace-hierarchy")
        assert resp.status_code == 200
        assert resp.text == ""
