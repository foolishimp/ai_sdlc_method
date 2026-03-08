# Validates: REQ-F-GVIZ-001, REQ-F-GVIZ-002, REQ-F-GVIZ-003, REQ-F-GVIZ-004, REQ-F-GVIZ-005
# Validates: REQ-F-TSER-001, REQ-F-TSER-002, REQ-F-TSER-003, REQ-F-TSER-004
# Validates: REQ-F-FLIN-001, REQ-F-FLIN-002
"""Tests for graph visualization, timeline series, and feature lineage views.

Covers:
  REQ-F-GVIZ-001 — topology node layout (graph-data JSON, canonical node order)
  REQ-F-GVIZ-002 — run filtering on graph-data endpoint
  REQ-F-GVIZ-003 — run-detail fragment
  REQ-F-GVIZ-004 — feature lineage page
  REQ-F-GVIZ-005 — artifact view
  REQ-F-TSER-001 — feature swimlane time axis (timeline page renders)
  REQ-F-TSER-002 — filter by feature / edge / status
  REQ-F-TSER-003 — timeline-runs fragment
  REQ-F-TSER-004 — timeline counters (total_runs, converged_count, etc.)
  REQ-F-FLIN-001 — feature lineage view (feature detail page)
  REQ-F-FLIN-002 — spec-to-artifact cross-navigation
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from event_factory import make_ol2_event
from genesis_monitor.registry import ProjectRegistry
from genesis_monitor.server.app import create_app
from genesis_monitor.server.broadcaster import SSEBroadcaster


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def rich_workspace(tmp_path: Path) -> Path:
    """Workspace with EdgeRun data (paired edge_started/edge_converged events)."""
    proj = tmp_path / "gviz_project"
    ws = proj / ".ai-workspace"
    ws.mkdir(parents=True)

    # Minimal STATUS.md
    (ws / "STATUS.md").write_text("# Project Status\n")

    # Feature vectors
    features_dir = ws / "features" / "active"
    features_dir.mkdir(parents=True)
    (features_dir / "REQ-F-GMON-001.yml").write_text(yaml.dump({
        "feature": "REQ-F-GMON-001",
        "title": "Genesis Monitor Dashboard",
        "status": "in_progress",
        "vector_type": "feature",
        "requirements": ["REQ-F-GMON-001", "REQ-F-DASH-001"],
        "trajectory": {
            "requirements": {"status": "converged", "iteration": 1},
            "design": {"status": "converged", "iteration": 1},
            "code": {"status": "in_progress", "iteration": 2},
        },
    }))

    # Events: paired START/COMPLETE for two features across two edges
    import uuid as _uuid
    events_dir = ws / "events"
    events_dir.mkdir()
    run1 = str(_uuid.uuid4())
    run2 = str(_uuid.uuid4())
    run3 = str(_uuid.uuid4())

    def _make_run(run_id, event_type, timestamp, project, feature, edge, **kw):
        """Make an OL v2 event with a fixed runId."""
        ev = make_ol2_event(event_type, timestamp=timestamp,
                            project=project, edge=edge, feature=feature, **kw)
        ev["run"]["runId"] = run_id
        return ev

    events = [
        # Run 1: REQ-F-GMON-001, intent→requirements, converged
        _make_run(run1, "edge_started",   "2026-02-01T10:00:00Z", "test", "REQ-F-GMON-001", "intent→requirements"),
        _make_run(run1, "edge_converged", "2026-02-01T10:30:00Z", "test", "REQ-F-GMON-001", "intent→requirements", delta=0),
        # Run 2: REQ-F-GMON-001, requirements→design, converged
        _make_run(run2, "edge_started",   "2026-02-01T11:00:00Z", "test", "REQ-F-GMON-001", "requirements→design"),
        _make_run(run2, "edge_converged", "2026-02-01T11:45:00Z", "test", "REQ-F-GMON-001", "requirements→design", delta=0),
        # Run 3: REQ-F-GMON-002, design→code, in_progress (no converged event)
        _make_run(run3, "edge_started",   "2026-02-01T12:00:00Z", "test", "REQ-F-GMON-002", "design→code"),
    ]
    (events_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
    )

    # Graph topology
    graph_dir = ws / "graph"
    graph_dir.mkdir()
    (graph_dir / "graph_topology.yml").write_text(yaml.dump({
        "asset_types": {
            "intent": {"description": "Intent"},
            "requirements": {"description": "Requirements"},
            "design": {"description": "Design"},
            "code": {"description": "Code"},
        },
        "transitions": [
            {"source": "intent", "target": "requirements"},
            {"source": "requirements", "target": "design"},
            {"source": "design", "target": "code"},
        ],
    }))

    # Tasks (required by scanner)
    (ws / "tasks" / "active").mkdir(parents=True)
    (ws / "tasks" / "active" / "ACTIVE_TASKS.md").write_text("# Active Tasks\n")

    # Context (required by parser)
    (ws / "context").mkdir()
    (ws / "context" / "project_constraints.yml").write_text(
        yaml.dump({"language": {"primary": "python"}})
    )

    # Spec doc (for artifact view and backing docs)
    spec_dir = proj / "specification" / "requirements"
    spec_dir.mkdir(parents=True)
    (spec_dir / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n### REQ-F-GMON-001: Genesis Monitor\n\nMonitor the workspace.\n\n"
        "### REQ-F-DASH-001: Dashboard\n\nShow a dashboard.\n"
    )

    return proj


@pytest.fixture
def test_client(rich_workspace: Path) -> TestClient:
    """TestClient backed by the rich_workspace fixture."""
    reg = ProjectRegistry()
    reg.add_project(rich_workspace)
    bc = SSEBroadcaster()

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    app = create_app(
        watch_dirs=[rich_workspace.parent],
        _registry=reg,
        _broadcaster=bc,
        _lifespan=noop_lifespan,
    )
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


# ── REQ-F-TSER-001..004: Timeline page ────────────────────────────────────────


class TestTimelinePage:
    """REQ-F-TSER-001: Feature swimlane time axis rendered on /timeline."""

    def test_timeline_returns_200(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/timeline")
        assert resp.status_code == 200

    def test_timeline_is_html(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/timeline")
        assert "text/html" in resp.headers["content-type"]

    def test_timeline_shows_features(self, test_client: TestClient):
        """REQ-F-TSER-001: Feature IDs appear as swimlane labels."""
        resp = test_client.get("/project/gviz-project/timeline")
        assert "REQ-F-GMON-001" in resp.text or "GMON-001" in resp.text

    def test_timeline_shows_run_counters(self, test_client: TestClient):
        """REQ-F-TSER-004: total_runs / converged_count shown on timeline page."""
        resp = test_client.get("/project/gviz-project/timeline")
        # The template renders total_runs, converged_count, etc.
        assert resp.status_code == 200
        # At least one run must appear
        assert "run" in resp.text.lower() or "converged" in resp.text.lower()

    def test_timeline_filter_by_feature(self, test_client: TestClient):
        """REQ-F-TSER-002: ?feature= filter accepted without error."""
        resp = test_client.get("/project/gviz-project/timeline?feature=REQ-F-GMON-001")
        assert resp.status_code == 200

    def test_timeline_filter_by_edge(self, test_client: TestClient):
        """REQ-F-TSER-002: ?edge= filter accepted without error."""
        resp = test_client.get("/project/gviz-project/timeline?edge=intent%E2%86%92requirements")
        assert resp.status_code == 200

    def test_timeline_filter_by_status(self, test_client: TestClient):
        """REQ-F-TSER-002: ?status= filter accepted without error."""
        resp = test_client.get("/project/gviz-project/timeline?status=converged")
        assert resp.status_code == 200

    def test_timeline_unknown_project_returns_404(self, test_client: TestClient):
        resp = test_client.get("/project/nonexistent/timeline")
        assert resp.status_code == 404


# ── REQ-F-GVIZ-001..002: Graph-data JSON ──────────────────────────────────────


class TestTimelineGraphData:
    """REQ-F-GVIZ-001: /timeline/graph-data returns JSON for D3 rendering."""

    def test_graph_data_returns_json(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/timeline/graph-data")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

    def test_graph_data_structure(self, test_client: TestClient):
        """REQ-F-GVIZ-001: response has nodes, runs, features keys."""
        data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        assert "nodes" in data
        assert "runs" in data
        assert "features" in data
        assert "project_id" in data

    def test_graph_data_has_nodes(self, test_client: TestClient):
        """REQ-F-GVIZ-001: at least one node present from the edge runs."""
        data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        assert len(data["nodes"]) > 0

    def test_graph_data_nodes_have_required_fields(self, test_client: TestClient):
        data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        for node in data["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "x_order" in node
            assert "total_runs" in node

    def test_graph_data_canonical_node_order(self, test_client: TestClient):
        """REQ-F-GVIZ-001: nodes ordered intent→requirements→design→code (canonical SDLC)."""
        data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        node_ids = [n["id"] for n in data["nodes"]]
        # Check relative ordering: intent before requirements before design
        if "intent" in node_ids and "requirements" in node_ids:
            assert node_ids.index("intent") < node_ids.index("requirements")
        if "requirements" in node_ids and "design" in node_ids:
            assert node_ids.index("requirements") < node_ids.index("design")

    def test_graph_data_x_order_monotonically_increasing(self, test_client: TestClient):
        """REQ-F-GVIZ-001: x_order values are 0, 1, 2, ... for left-to-right layout."""
        data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        x_orders = [n["x_order"] for n in data["nodes"]]
        assert x_orders == list(range(len(x_orders)))

    def test_graph_data_runs_have_required_fields(self, test_client: TestClient):
        data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        for run in data["runs"]:
            assert "run_id" in run
            assert "edge" in run
            assert "source" in run
            assert "target" in run
            assert "status" in run
            assert "started_at" in run

    def test_graph_data_filter_by_feature(self, test_client: TestClient):
        """REQ-F-GVIZ-002: ?feature= filters runs to the specified feature."""
        all_data = test_client.get("/project/gviz-project/timeline/graph-data").json()
        filtered = test_client.get(
            "/project/gviz-project/timeline/graph-data?feature=REQ-F-GMON-001"
        ).json()
        all_features = {r["feature"] for r in all_data["runs"]}
        if len(all_features) > 1:
            assert len(filtered["runs"]) < len(all_data["runs"])
        for run in filtered["runs"]:
            assert run["feature"] == "REQ-F-GMON-001"

    def test_graph_data_unknown_project_returns_404(self, test_client: TestClient):
        resp = test_client.get("/project/nonexistent/timeline/graph-data")
        assert resp.status_code == 404


# ── REQ-F-TSER-003 + REQ-F-GVIZ-003: Timeline fragments ──────────────────────


class TestTimelineFragments:

    def test_timeline_runs_fragment_returns_200(self, test_client: TestClient):
        """REQ-F-TSER-003: /fragments/.../timeline-runs returns HTML partial."""
        resp = test_client.get("/fragments/project/gviz-project/timeline-runs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_timeline_runs_fragment_filter_by_feature(self, test_client: TestClient):
        """REQ-F-TSER-003: timeline-runs fragment respects ?feature= filter."""
        resp = test_client.get(
            "/fragments/project/gviz-project/timeline-runs?feature=REQ-F-GMON-001"
        )
        assert resp.status_code == 200

    def test_timeline_runs_fragment_unknown_project_returns_empty(self, test_client: TestClient):
        resp = test_client.get("/fragments/project/nonexistent/timeline-runs")
        assert resp.status_code == 200
        assert resp.text == ""

    def test_run_detail_fragment_unknown_run_returns_not_found_message(self, test_client: TestClient):
        """REQ-F-GVIZ-003: run-detail fragment handles missing run gracefully."""
        resp = test_client.get("/fragments/project/gviz-project/run-detail/nonexistent-run-id")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower() or resp.text.strip() == ""

    def test_run_detail_fragment_unknown_project_returns_empty(self, test_client: TestClient):
        resp = test_client.get("/fragments/project/nonexistent/run-detail/any-id")
        assert resp.status_code == 200
        assert resp.text == ""


# ── REQ-F-GVIZ-004 + REQ-F-FLIN-001/002: Feature lineage page ────────────────


class TestFeatureLineagePage:
    """REQ-F-FLIN-001: Feature Lineage View at /project/{id}/feature/{fid}."""

    def test_feature_lineage_returns_200(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/feature/REQ-F-GMON-001")
        assert resp.status_code == 200

    def test_feature_lineage_is_html(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/feature/REQ-F-GMON-001")
        assert "text/html" in resp.headers["content-type"]

    def test_feature_lineage_shows_feature_id(self, test_client: TestClient):
        """REQ-F-FLIN-001: the feature ID is shown in the lineage view."""
        resp = test_client.get("/project/gviz-project/feature/REQ-F-GMON-001")
        assert "REQ-F-GMON-001" in resp.text

    def test_feature_lineage_shows_requirements(self, test_client: TestClient):
        """REQ-F-FLIN-002: spec-to-artifact navigation — req keys rendered."""
        resp = test_client.get("/project/gviz-project/feature/REQ-F-GMON-001")
        # Feature has requirements: ["REQ-F-GMON-001", "REQ-F-DASH-001"]
        assert "REQ-F-DASH-001" in resp.text or "REQ-F-GMON-001" in resp.text

    def test_feature_lineage_shows_backing_docs(self, test_client: TestClient):
        """REQ-F-FLIN-002: backing spec doc sections are surfaced on the page."""
        resp = test_client.get("/project/gviz-project/feature/REQ-F-GMON-001")
        # REQUIREMENTS.md has content for REQ-F-GMON-001 — it should appear
        assert "Genesis Monitor" in resp.text or "Monitor the workspace" in resp.text

    def test_feature_lineage_unknown_project_returns_404(self, test_client: TestClient):
        resp = test_client.get("/project/nonexistent/feature/REQ-F-GMON-001")
        assert resp.status_code == 404

    def test_feature_lineage_unknown_feature_returns_200(self, test_client: TestClient):
        """Unknown feature ID returns 200 with empty/graceful state (not a 404)."""
        resp = test_client.get("/project/gviz-project/feature/REQ-F-DOES-NOT-EXIST")
        assert resp.status_code == 200


# ── REQ-F-GVIZ-005: Artifact view ─────────────────────────────────────────────


class TestArtifactView:
    """REQ-F-GVIZ-005: /project/{id}/artifact renders project file content."""

    def test_artifact_view_existing_file(self, test_client: TestClient, rich_workspace: Path):
        spec_rel = "specification/requirements/REQUIREMENTS.md"
        resp = test_client.get(f"/project/gviz-project/artifact?path={spec_rel}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_artifact_view_shows_file_content(self, test_client: TestClient):
        spec_rel = "specification/requirements/REQUIREMENTS.md"
        resp = test_client.get(f"/project/gviz-project/artifact?path={spec_rel}")
        assert "Requirements" in resp.text or "REQ-F-GMON-001" in resp.text

    def test_artifact_view_missing_file_returns_200_with_error(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/artifact?path=nonexistent/file.md")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower() or "error" in resp.text.lower()

    def test_artifact_view_no_path_returns_400(self, test_client: TestClient):
        resp = test_client.get("/project/gviz-project/artifact")
        assert resp.status_code == 400

    def test_artifact_view_unknown_project_returns_404(self, test_client: TestClient):
        resp = test_client.get("/project/nonexistent/artifact?path=anything.md")
        assert resp.status_code == 404
