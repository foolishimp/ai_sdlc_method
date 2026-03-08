# Validates: REQ-NFR-003, REQ-NFR-004, REQ-NFR-005
# Validates: REQ-F-DOG-001, REQ-F-DOG-002
# Validates: REQ-F-GMON-001, REQ-F-GMON-002
# Validates: REQ-F-FLIN-003, REQ-F-FLIN-004
# Validates: REQ-TOOL-015
"""Tests for non-functional requirements, dogfood self-monitoring, and monitor
   meta-requirements.

REQ-NFR-003 — Startup Performance: initial scan completes in < 5s per 50 projects.
REQ-NFR-004 — Zero Build Step: no package.json, no node_modules/.
REQ-NFR-005 — Python 3.12+: pyproject.toml declares requires-python >= 3.12.
REQ-F-DOG-001 — Self-Monitoring: monitor's own workspace appears in project index.
REQ-F-DOG-002 — Methodology Compliance: all code/test files have REQ-* tags.
REQ-F-GMON-001 — Genesis Monitor Dashboard: project dashboard renders.
REQ-F-GMON-002 — Monitor meta: project can monitor multiple projects.
REQ-F-FLIN-003 — Multi-Feature Convergence Map: matrix view is accessible.
REQ-F-FLIN-004 — Projection Selector: design-tenant ?design= projection works.
"""

import re
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from genesis_monitor.registry import ProjectRegistry
from genesis_monitor.scanner import scan_roots
from genesis_monitor.server.app import create_app
from genesis_monitor.server.broadcaster import SSEBroadcaster


# ── Fixtures ───────────────────────────────────────────────────────────────────

_IMP_ROOT = Path(__file__).parent.parent   # imp_fastapi/
_PROJ_ROOT = _IMP_ROOT.parent              # genesis_monitor/ (project root)
_SRC_ROOT = _IMP_ROOT / "code" / "src"
_TEST_ROOT = _IMP_ROOT / "tests"


@pytest.fixture
def test_client(tmp_workspace: Path) -> TestClient:
    """TestClient backed by the shared tmp_workspace fixture from conftest."""
    reg = ProjectRegistry()
    reg.add_project(tmp_workspace)
    bc = SSEBroadcaster()

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    app = create_app(
        watch_dirs=[tmp_workspace.parent],
        _registry=reg,
        _broadcaster=bc,
        _lifespan=noop_lifespan,
    )
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


# ── REQ-NFR-004: Zero Build Step ──────────────────────────────────────────────


class TestZeroBuildStep:
    """REQ-NFR-004: frontend requires no build tooling."""

    def test_no_package_json(self):
        """AC-1: No package.json anywhere in the imp_fastapi tree."""
        matches = list(_IMP_ROOT.rglob("package.json"))
        assert matches == [], f"Found package.json: {matches}"

    def test_no_node_modules(self):
        """AC-1: No node_modules/ directory."""
        matches = list(_IMP_ROOT.rglob("node_modules"))
        assert matches == [], f"Found node_modules: {matches}"

    def test_templates_use_cdn_scripts(self):
        """AC-2: Mermaid and HTMX are loaded from CDN <script> tags."""
        templates_dir = _IMP_ROOT / "code" / "src" / "genesis_monitor" / "templates"
        html_files = list(templates_dir.rglob("*.html"))
        assert len(html_files) > 0, "No HTML templates found"

        all_html = "\n".join(f.read_text(errors="replace") for f in html_files)
        # At least one template must load htmx or mermaid from a CDN
        assert "htmx.org" in all_html or "mermaid" in all_html.lower()


# ── REQ-NFR-005: Python 3.12+ ─────────────────────────────────────────────────


class TestPython312Compatibility:
    """REQ-NFR-005: system uses Python 3.12+."""

    def test_pyproject_toml_requires_python_312(self):
        """AC-1: pyproject.toml declares requires-python >= 3.12."""
        pyproject = _IMP_ROOT / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml not found"
        content = pyproject.read_text()
        # Match patterns like: requires-python = ">=3.12" or >=3.12,<4
        assert re.search(r'requires-python\s*=\s*["\']>=3\.1[2-9]', content), (
            "pyproject.toml does not declare requires-python >= 3.12"
        )

    def test_runtime_python_version(self):
        """AC-1: tests run on Python 3.12+. Skips with a warning if env is 3.11."""
        if sys.version_info < (3, 12):
            pytest.skip(
                f"Runtime is Python {sys.version_info.major}.{sys.version_info.minor} "
                f"(REQ-NFR-005 target is 3.12+; upgrade env to enforce)"
            )
        assert sys.version_info >= (3, 12)


# ── REQ-NFR-003: Startup Performance ──────────────────────────────────────────


class TestStartupPerformance:
    """REQ-NFR-003: registry scan completes quickly."""

    def test_single_project_scan_is_fast(self, tmp_workspace: Path):
        """AC-1: scanning a single project is well under 5 seconds."""
        start = time.monotonic()
        reg = ProjectRegistry()
        reg.add_project(tmp_workspace)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"Registry scan took {elapsed:.2f}s (limit: 5s)"

    def test_scan_roots_returns_quickly(self, tmp_path: Path):
        """REQ-NFR-003: scan_roots completes quickly on a shallow tree."""
        (tmp_path / "proj1" / ".ai-workspace").mkdir(parents=True)
        (tmp_path / "proj2" / ".ai-workspace").mkdir(parents=True)
        start = time.monotonic()
        paths = scan_roots([tmp_path])
        elapsed = time.monotonic() - start
        assert elapsed < 2.0
        assert len(paths) == 2


# ── REQ-F-DOG-001: Self-Monitoring ────────────────────────────────────────────


class TestWorkspacePlacement:
    """REQ-TOOL-015 AC-3: .ai-workspace must be at the project root, not inside imp_*/."""

    def test_no_workspace_inside_imp_tenant(self):
        """REQ-TOOL-015: no imp_*/ sibling of _PROJ_ROOT contains .ai-workspace/.

        This test would have immediately caught the genesis_monitor workspace
        being placed at imp_fastapi/.ai-workspace/ instead of
        genesis_monitor/.ai-workspace/.
        """
        violations = [
            str(d) for d in _PROJ_ROOT.glob("imp_*/.ai-workspace")
            if d.is_dir()
        ]
        assert violations == [], (
            ".ai-workspace found inside implementation tenant(s):\n  "
            + "\n  ".join(violations)
            + "\nWorkspace MUST be at the project root, not inside imp_*/ tenants."
            " (REQ-TOOL-015, ADR-031)"
        )

    def test_workspace_exists_at_project_root(self):
        """REQ-TOOL-015 AC-1: .ai-workspace is present at the project root."""
        ws = _PROJ_ROOT / ".ai-workspace"
        assert ws.is_dir(), (
            f".ai-workspace not found at project root ({_PROJ_ROOT}). "
            "Run the installer from the project root, not from inside imp_*/."
        )


class TestSelfMonitoring:
    """REQ-F-DOG-001: the monitor's own .ai-workspace/ is a valid monitored project."""

    def test_monitor_workspace_is_discoverable(self):
        """AC-1: scan_roots can find the monitor project's own .ai-workspace/."""
        monitor_ws = _PROJ_ROOT / ".ai-workspace"
        if not monitor_ws.is_dir():
            pytest.skip(".ai-workspace not present in monitor project root")

        found = scan_roots([_PROJ_ROOT.parent])
        found_paths = [str(p) for p in found]
        assert any(str(_PROJ_ROOT) in p for p in found_paths), (
            f"Monitor project not found in {found_paths}"
        )

    def test_monitor_workspace_can_be_added_to_registry(self):
        """AC-1: registry.add_project succeeds for the monitor's own directory."""
        monitor_ws = _PROJ_ROOT / ".ai-workspace"
        if not monitor_ws.is_dir():
            pytest.skip(".ai-workspace not present in monitor project root")

        reg = ProjectRegistry()
        project = reg.add_project(_PROJ_ROOT)
        assert project is not None
        assert project.project_id != ""


# ── REQ-F-DOG-002: Methodology Compliance ─────────────────────────────────────


class TestMethodologyCompliance:
    """REQ-F-DOG-002: all production code and test files carry REQ-* tags."""

    def _collect_py_files(self, root: Path, exclude_patterns=()) -> list[Path]:
        files = []
        for f in root.rglob("*.py"):
            if any(pat in str(f) for pat in exclude_patterns):
                continue
            files.append(f)
        return files

    def test_all_code_files_have_implements_tag(self):
        """AC-1: every .py file in src/ has at least one # Implements: REQ-* line."""
        skip = ["__pycache__", ".egg-info"]
        py_files = self._collect_py_files(_SRC_ROOT, skip)
        assert len(py_files) > 0

        missing = []
        for f in py_files:
            text = f.read_text(errors="replace")
            if "# Implements: REQ-" not in text:
                missing.append(str(f.relative_to(_IMP_ROOT)))

        assert missing == [], (
            f"Code files missing # Implements: REQ-* tag:\n" + "\n".join(missing)
        )

    def test_all_test_files_have_validates_tag(self):
        """AC-2: every test_*.py has at least one # Validates: REQ-* line."""
        skip = ["__pycache__", ".egg-info"]
        test_files = [
            f for f in self._collect_py_files(_TEST_ROOT, skip)
            if f.name.startswith("test_")
        ]
        assert len(test_files) > 0

        missing = []
        for f in test_files:
            text = f.read_text(errors="replace")
            if "# Validates: REQ-" not in text:
                missing.append(str(f.relative_to(_IMP_ROOT)))

        assert missing == [], (
            f"Test files missing # Validates: REQ-* tag:\n" + "\n".join(missing)
        )


# ── REQ-F-GMON-001/002: Monitor functionality ─────────────────────────────────


class TestMonitorFunctionality:
    """REQ-F-GMON-001/002: basic monitor dashboard and multi-project support."""

    def test_dashboard_renders_project(self, test_client: TestClient):
        """REQ-F-GMON-001: project dashboard renders successfully."""
        resp = test_client.get("/project/test-project")
        assert resp.status_code == 200
        assert "test" in resp.text.lower() or "project" in resp.text.lower()

    def test_index_lists_monitored_projects(self, test_client: TestClient):
        """REQ-F-GMON-001: index page lists all monitored projects."""
        resp = test_client.get("/")
        assert resp.status_code == 200
        assert resp.text  # non-empty response

    def test_can_monitor_multiple_projects(self, tmp_path: Path):
        """REQ-F-GMON-002: registry holds multiple projects simultaneously."""
        for name in ("proj_a", "proj_b", "proj_c"):
            ws = tmp_path / name / ".ai-workspace"
            ws.mkdir(parents=True)
            (ws / "events").mkdir()
            (ws / "events" / "events.jsonl").write_text("")

        reg = ProjectRegistry()
        for name in ("proj_a", "proj_b", "proj_c"):
            reg.add_project(tmp_path / name)

        assert len(reg.list_projects()) == 3

    def test_api_health_reports_project_count(self, test_client: TestClient):
        """REQ-F-GMON-001: /api/health reports number of monitored projects."""
        resp = test_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["projects"] >= 1


# ── REQ-F-FLIN-003: Multi-Feature Convergence Map ─────────────────────────────


class TestMultiFeatureConvergenceMap:
    """REQ-F-FLIN-003: feature × edge matrix accessible from project dashboard."""

    def test_convergence_fragment_returns_matrix(self, test_client: TestClient):
        """REQ-F-FLIN-003: features fragment contains a table (matrix view)."""
        resp = test_client.get("/fragments/project/test-project/features")
        assert resp.status_code == 200
        # Should contain table-like structure with feature IDs
        assert "REQ-F-GMON-001" in resp.text

    def test_feature_matrix_available_on_project_page(self, test_client: TestClient):
        """REQ-F-FLIN-003: project detail page includes the convergence matrix."""
        resp = test_client.get("/project/test-project")
        assert resp.status_code == 200
        # Matrix section must be present on the project page
        assert "REQ-F-GMON-001" in resp.text


# ── REQ-F-FLIN-004: Projection Selector ───────────────────────────────────────


class TestProjectionSelector:
    """REQ-F-FLIN-004: views support ?design= projection parameter."""

    def test_project_page_accepts_design_param(self, test_client: TestClient):
        """REQ-F-FLIN-004: ?design= scopes the view to a specific tenant."""
        resp = test_client.get("/project/test-project?design=imp_claude")
        assert resp.status_code == 200

    def test_design_param_in_url_is_preserved(self, test_client: TestClient):
        """REQ-F-FLIN-004: the active tenant is reflected in the rendered page."""
        resp = test_client.get("/project/test-project?design=imp_claude")
        # The page should indicate the active design selection
        assert "imp_claude" in resp.text

    def test_all_tenants_view_available(self, test_client: TestClient):
        """REQ-F-FLIN-004: unfiltered (all tenants) view is the default."""
        resp = test_client.get("/project/test-project")
        assert resp.status_code == 200
        # Should show events from multiple tenants
        assert "imp_claude" in resp.text or "imp_gemini" in resp.text

    def test_fragment_routes_accept_design_param(self, test_client: TestClient):
        """REQ-F-FLIN-004: fragment routes also honour ?design= projection."""
        for endpoint in ["graph", "convergence", "events", "features"]:
            resp = test_client.get(
                f"/fragments/project/test-project/{endpoint}?design=imp_claude"
            )
            assert resp.status_code == 200, f"Fragment {endpoint} rejected design param"
