# Validates: REQ-EVAL-001, REQ-EVAL-002, REQ-TOOL-005
"""V0.4 gate: validate an archived headless-Claude convergence run.

Unlike test_e2e_convergence.py (which spawns a new Claude subprocess),
these tests validate the LATEST archived run in runs/ against the same
convergence criteria. This proves the methodology was applied to an
external project and produced valid, converging, test-passing output
WITHOUT re-running the expensive headless subprocess.

Gate criteria (v0.4 — ecosystem verified):
  1. Feature vector fully converged (all standard profile edges)
  2. Events: edge_started, edge_converged, iteration_completed all present
  3. Delta trace reaches 0 (homeostatic closure)
  4. Generated source files have Implements: REQ tags
  5. Generated test files have Validates: REQ tags
  6. Generated tests PASS when run via pytest

Run:
    pytest imp_claude/tests/e2e/test_e2e_archived_convergence.py -v
"""

import json
import pathlib
import subprocess

import pytest

# ── Paths ─────────────────────────────────────────────────────────────
_E2E_DIR = pathlib.Path(__file__).parent
RUNS_DIR = _E2E_DIR / "runs"
LATEST_RUN = RUNS_DIR / "e2e_latest"

skip_no_run = pytest.mark.skipif(
    not LATEST_RUN.exists(),
    reason="No archived e2e run at runs/e2e_latest — run /gen-iterate on a project first",
)


@pytest.fixture(scope="module")
def run_dir() -> pathlib.Path:
    """Resolve e2e_latest symlink to the actual archived run directory."""
    resolved = LATEST_RUN.resolve()
    assert resolved.is_dir(), f"e2e_latest does not resolve to a directory: {resolved}"
    return resolved


@pytest.fixture(scope="module")
def run_events(run_dir: pathlib.Path) -> list[dict]:
    """Load events.jsonl from the archived run."""
    events_file = run_dir / ".ai-workspace" / "events" / "events.jsonl"
    assert events_file.exists(), f"events.jsonl missing from archived run: {events_file}"
    events = []
    with open(events_file) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


@pytest.fixture(scope="module")
def run_feature_vector(run_dir: pathlib.Path) -> dict:
    """Load the primary feature vector from the archived run."""
    active = run_dir / ".ai-workspace" / "features" / "active"
    ymls = list(active.glob("*.yml")) if active.exists() else []
    assert ymls, f"No feature vector found in {active}"
    import yaml
    return yaml.safe_load(ymls[0].read_text())


# ═══════════════════════════════════════════════════════════════════════
# V0.4 GATE TESTS
# ═══════════════════════════════════════════════════════════════════════

@skip_no_run
class TestArchivedConvergence:
    """V0.4 gate — archived run proves methodology applied to external project."""

    def test_run_directory_exists(self, run_dir):
        """The archived run resolves to a real directory."""
        assert run_dir.is_dir(), f"Expected run directory at {run_dir}"

    def test_feature_vector_status_converged(self, run_feature_vector):
        """The primary feature must be fully converged."""
        status = run_feature_vector.get("status")
        assert status == "converged", (
            f"Feature vector status is '{status}' — expected 'converged'. "
            "The methodology must drive the feature to full convergence for v0.4."
        )

    def test_all_trajectory_edges_converged(self, run_feature_vector):
        """Every trajectory edge must report status: converged."""
        trajectory = run_feature_vector.get("trajectory", {})
        assert trajectory, "Feature vector has no trajectory section"
        for edge, edge_data in trajectory.items():
            edge_status = edge_data.get("status")
            assert edge_status == "converged", (
                f"Trajectory edge '{edge}' is '{edge_status}' — expected 'converged'. "
                "All profile edges must converge for v0.4."
            )

    def test_events_contain_edge_converged(self, run_events):
        """At least one edge_converged event must be present."""
        converged = [e for e in run_events if e.get("event_type") == "edge_converged"]
        assert converged, (
            "No edge_converged events found in events.jsonl — "
            "the methodology must emit convergence events"
        )

    def test_events_contain_iteration_completed(self, run_events):
        """At least one iteration_completed event must be present."""
        completed = [e for e in run_events if e.get("event_type") == "iteration_completed"]
        assert completed, "No iteration_completed events found in events.jsonl"

    def test_events_delta_reaches_zero(self, run_events):
        """At least one iteration must converge with delta=0."""
        completed = [e for e in run_events if e.get("event_type") == "iteration_completed"]
        deltas = [e.get("delta", -1) for e in completed]
        assert 0 in deltas, (
            f"No iteration_completed event with delta=0 found. "
            f"Observed deltas: {deltas}. "
            "Homeostatic closure requires delta reaching 0."
        )

    def test_events_all_started_edges_converged(self, run_events):
        """Every edge that was started must also have a converged event."""
        started = {e.get("edge") for e in run_events if e.get("event_type") == "edge_started"}
        converged = {e.get("edge") for e in run_events if e.get("event_type") == "edge_converged"}
        unconverged = started - converged
        assert not unconverged, (
            f"Edges started but not converged: {unconverged}. "
            "All active edges must reach convergence."
        )

    def test_source_files_have_implements_tags(self, run_dir):
        """Generated source files must have Implements: REQ-* tags."""
        src_dir = run_dir / "src"
        if not src_dir.exists():
            pytest.skip("No src/ directory in archived run")
        py_files = list(src_dir.rglob("*.py"))
        assert py_files, f"No Python source files found in {src_dir}"
        tagged = [f for f in py_files if "Implements:" in f.read_text()]
        assert tagged, (
            f"No source files with 'Implements:' tags found in {src_dir}. "
            "REQ-key traceability requires Implements: tags in production code."
        )

    def test_test_files_have_validates_tags(self, run_dir):
        """Generated test files must have Validates: REQ-* tags."""
        tests_dir = run_dir / "tests"
        if not tests_dir.exists():
            pytest.skip("No tests/ directory in archived run")
        py_files = [f for f in tests_dir.rglob("*.py") if f.name.startswith("test_")]
        assert py_files, f"No test files found in {tests_dir}"
        tagged = [f for f in py_files if "Validates:" in f.read_text()]
        assert tagged, (
            f"No test files with 'Validates:' tags found in {tests_dir}. "
            "REQ-key traceability requires Validates: tags in test code."
        )

    def test_generated_tests_pass(self, run_dir):
        """The generated tests must all pass — deterministic verification."""
        tests_dir = run_dir / "tests"
        if not tests_dir.exists():
            pytest.skip("No tests/ directory in archived run")
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_dir), "-q", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=str(run_dir),
            timeout=60,
        )
        assert result.returncode == 0, (
            f"Generated tests FAILED in archived run. "
            f"pytest exit code: {result.returncode}\n"
            f"stdout:\n{result.stdout[-2000:]}\n"
            f"stderr:\n{result.stderr[-500:]}"
        )
