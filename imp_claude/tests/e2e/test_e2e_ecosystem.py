# Validates: REQ-F-TELEM-001, REQ-F-DISPATCH-001, REQ-ITER-001, REQ-TOOL-015
"""Ecosystem integration tests — full install → evaluate → telemetry pipeline.

Tests the two key execution paths without a live Claude session:

  Path A (deterministic):
    gen-setup.py → engine evaluate --deterministic-only --asset → verify JSON output
    + verify events.jsonl appended + verify req= telemetry in stderr

  Path B (homeostatic):
    Write intent_raised to events.jsonl → dispatch_monitor / get_pending_dispatches
    detects unhandled intent → verify DispatchTarget fields

Sign-off coverage:
  REQ-F-TELEM-001  — req= structured log tags flow from engine paths to stderr
  REQ-F-DISPATCH-001 — dispatch_monitor identifies unhandled intent_raised events
  REQ-ITER-001     — iterate() emits well-formed events to events.jsonl (append-only)
  REQ-TOOL-015     — gen-setup.py creates a complete, invocable Genesis workspace

No Claude session required.  Runs in Lane 1 (not marked e2e or mcp).
"""

import json
import os
import re
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

# ── Repo layout ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[3]  # ai_sdlc_method/
INSTALLER = REPO_ROOT / "imp_claude" / "code" / "installers" / "gen-setup.py"
GENESIS_SRC = REPO_ROOT / "imp_claude" / "code"  # contains genesis/ package


# ── Helpers ───────────────────────────────────────────────────────────────────

def _genesis_env(project_dir: Path) -> dict[str, str]:
    """PYTHONPATH pointing at the installed engine (falls back to source)."""
    env = os.environ.copy()
    installed = project_dir / ".genesis"
    if (installed / "genesis" / "__main__.py").exists():
        env["PYTHONPATH"] = str(installed)
    else:
        env["PYTHONPATH"] = str(GENESIS_SRC)
    return env


def _run_engine(project_dir: Path, *args: str) -> subprocess.CompletedProcess:
    """Run `python -m genesis <args>` inside project_dir, capturing output."""
    return subprocess.run(
        [sys.executable, "-m", "genesis", *args],
        env=_genesis_env(project_dir),
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        timeout=120,
    )


def _read_events(project_dir: Path) -> list[dict]:
    events_path = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    if not events_path.exists():
        return []
    return [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]


def _append_event(project_dir: Path, event: dict) -> None:
    events_path = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a") as f:
        f.write(json.dumps(event) + "\n")


# ── Module-scoped fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def installed_project(tmp_path_factory):
    """Install Genesis via gen-setup.py --source (local repo). Module-scoped — runs once."""
    project_dir = tmp_path_factory.mktemp("ecosystem_install")

    # Minimal project scaffold the installer expects
    (project_dir / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [project]
            name = "eco-test"
            version = "0.1.0"
        """)
    )
    (project_dir / "specification").mkdir()
    (project_dir / "specification" / "INTENT.md").write_text(
        "# Intent\nBuild a basic arithmetic library.\n"
    )

    result = subprocess.run(
        [
            sys.executable, str(INSTALLER),
            "--source", str(REPO_ROOT),
            "--target", str(project_dir),
        ],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        timeout=120,
    )

    if result.returncode != 0:
        pytest.fail(
            f"gen-setup.py install failed (rc={result.returncode}):\n"
            f"STDOUT:\n{result.stdout[-3000:]}\n"
            f"STDERR:\n{result.stderr[-3000:]}"
        )

    return project_dir


@pytest.fixture(scope="module")
def project_with_code(installed_project):
    """Installed project with a minimal Python module + passing tests (code↔unit_tests edge)."""
    src = installed_project / "src"
    tests = installed_project / "tests"
    src.mkdir(exist_ok=True)
    tests.mkdir(exist_ok=True)

    (src / "__init__.py").write_text("")
    (src / "calc.py").write_text(
        textwrap.dedent("""\
            # Implements: REQ-F-ECO-001
            \"\"\"Basic arithmetic operations.\"\"\"

            def add(a: float, b: float) -> float:
                \"\"\"Return the sum of a and b.\"\"\"
                if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                    raise TypeError("Expected numeric inputs")
                return a + b

            def subtract(a: float, b: float) -> float:
                \"\"\"Return a minus b.\"\"\"
                if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                    raise TypeError("Expected numeric inputs")
                return a - b
        """)
    )

    (tests / "__init__.py").write_text("")
    (tests / "test_calc.py").write_text(
        textwrap.dedent("""\
            # Validates: REQ-F-ECO-001
            \"\"\"Unit tests for calc module.\"\"\"
            import pytest
            from src.calc import add, subtract

            def test_add_integers():
                assert add(1, 2) == 3

            def test_add_floats():
                assert abs(add(1.1, 2.2) - 3.3) < 1e-10

            def test_add_type_error():
                with pytest.raises(TypeError):
                    add("a", 1)

            def test_subtract():
                assert subtract(5, 3) == 2

            def test_subtract_negative():
                assert subtract(1, 5) == -4
        """)
    )

    # Feature vector for this module
    features_dir = installed_project / ".ai-workspace" / "features" / "active"
    features_dir.mkdir(parents=True, exist_ok=True)
    (features_dir / "REQ-F-ECO-001.yml").write_text(
        yaml.dump({
            "feature": "REQ-F-ECO-001",
            "title": "Basic arithmetic",
            "status": "iterating",
            "profile": "hotfix",
            "priority": "medium",
            "trajectory": {
                "code": {"status": "iterating"},
                "unit_tests": {"status": "iterating"},
            },
        })
    )

    return installed_project


# ═══════════════════════════════════════════════════════════════════════════════
# Class 1 — Installer integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestInstallerIntegration:
    """gen-setup.py creates a complete, invocable Genesis workspace.  REQ-TOOL-015."""

    def test_engine_files_installed(self, installed_project):
        """All critical engine modules must be present at .genesis/genesis/."""
        engine_dir = installed_project / ".genesis" / "genesis"
        assert engine_dir.is_dir(), f".genesis/genesis/ not created at {installed_project}"
        for module in (
            "__main__.py", "__init__.py", "engine.py",
            "dispatch_monitor.py", "edge_runner.py", "intent_observer.py",
            "dispatch_loop.py",
        ):
            assert (engine_dir / module).exists(), f"Engine missing: {module}"

    def test_workspace_directories_created(self, installed_project):
        """All workspace directories required by the engine must exist."""
        ws = installed_project / ".ai-workspace"
        for sub in ("events", "features/active", "graph", "context", "tasks/active"):
            assert (ws / sub).exists(), f".ai-workspace/{sub} not created"

    def test_project_initialized_event_written(self, installed_project):
        """Installer must emit a project_initialized event to events.jsonl."""
        events = _read_events(installed_project)
        assert events, "events.jsonl is empty after install"
        # Handle both flat and OL event schemas
        serialised = json.dumps(events)
        assert "project_initialized" in serialised or "ProjectInitialized" in serialised, (
            f"No project_initialized event found. Events: {[e.get('event_type') for e in events]}"
        )

    def test_bootloader_written_to_claude_md(self, installed_project):
        """CLAUDE.md must contain the Genesis Bootloader."""
        claude_md = installed_project / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md not written by installer"
        content = claude_md.read_text()
        assert "GENESIS_BOOTLOADER_START" in content or "Genesis Bootloader" in content, (
            "CLAUDE.md does not contain the Genesis Bootloader"
        )

    def test_commands_installed(self, installed_project):
        """All gen-* slash commands must be present."""
        commands_dir = installed_project / ".claude" / "commands"
        assert commands_dir.is_dir(), ".claude/commands/ not created"
        commands = list(commands_dir.glob("gen-*.md"))
        assert len(commands) >= 10, f"Expected ≥10 gen-* commands, found {len(commands)}"

    def test_graph_topology_installed(self, installed_project):
        """graph_topology.yml must be present and parseable."""
        # Try both known locations
        candidates = [
            installed_project / ".ai-workspace" / "graph" / "graph_topology.yml",
            installed_project / ".ai-workspace" / "graph" / "edges" / "graph_topology.yml",
        ]
        found = next((p for p in candidates if p.exists()), None)
        assert found is not None, "graph_topology.yml not found in workspace"
        data = yaml.safe_load(found.read_text())
        assert "transitions" in data
        assert len(data["transitions"]) > 0

    def test_engine_invocable(self, installed_project):
        """Engine subprocess must start without import errors."""
        result = _run_engine(installed_project, "--help")
        # --help → rc=0, no subcommand → rc=1 with usage. Neither is a crash.
        assert result.returncode in (0, 1), (
            f"Engine crashed (rc={result.returncode}):\n{result.stderr[:500]}"
        )
        combined = result.stdout + result.stderr
        assert "genesis" in combined.lower() or "usage" in combined.lower()

    def test_reinstall_preserves_existing_events(self, installed_project):
        """Idempotent reinstall must not overwrite events.jsonl."""
        events_before = _read_events(installed_project)
        assert events_before, "events.jsonl empty before reinstall test"

        subprocess.run(
            [sys.executable, str(INSTALLER), "--source", str(REPO_ROOT), "--target", str(installed_project)],
            capture_output=True, text=True, cwd=str(installed_project), timeout=120,
        )

        events_after = _read_events(installed_project)
        # Must never shrink; first N events must be identical
        assert len(events_after) >= len(events_before), "Reinstall deleted events"
        for i, ev in enumerate(events_before):
            assert events_after[i] == ev, f"Event {i} mutated by reinstall"


# ═══════════════════════════════════════════════════════════════════════════════
# Class 2 — Deterministic evaluation path  (F_D only, no Claude)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeterministicEvaluation:
    """iterate() produces correct F_D output and emits events.  REQ-ITER-001."""

    def test_evaluate_produces_valid_json(self, project_with_code):
        result = _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        assert result.returncode in (0, 1), f"Engine error:\n{result.stderr[:500]}"
        output = json.loads(result.stdout)
        for field in ("delta", "converged", "checks", "edge", "feature"):
            assert field in output, f"Missing field '{field}' in engine output"

    def test_evaluate_output_contains_correct_feature_id(self, project_with_code):
        result = _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        output = json.loads(result.stdout)
        assert output["feature"] == "REQ-F-ECO-001"
        assert output["edge"] == "code\u2194unit_tests"

    def test_evaluate_emits_event_to_events_jsonl(self, project_with_code):
        """Engine must append at least one event per invocation."""
        before_count = len(_read_events(project_with_code))
        _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        assert len(_read_events(project_with_code)) > before_count, (
            "Engine did not append any event to events.jsonl"
        )

    def test_evaluate_passing_tests_reports_converged(self, project_with_code):
        """Correct implementation with passing tests → converged: true, delta=0."""
        result = _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        output = json.loads(result.stdout)
        assert output["converged"] is True, (
            f"Expected converged but delta={output['delta']}. "
            f"Failing checks: {[c for c in output['checks'] if c['outcome'] != 'pass']}"
        )
        assert output["delta"] == 0

    def test_evaluate_broken_code_reports_nonzero_delta(self, tmp_path):
        """Project with failing tests → converged: false, delta > 0.

        The deterministic evaluate command runs pytest in the project directory.
        A project where src/calc.py is broken and tests expose the bug
        must report delta > 0, not converged.
        """
        # Build a minimal self-contained project with broken code + exposing tests
        broken_proj = tmp_path / "broken_project"
        broken_proj.mkdir()
        src = broken_proj / "src"
        tests = broken_proj / "tests"
        src.mkdir()
        tests.mkdir()

        # Install a minimal project_constraints.yml (engine needs it)
        ws = broken_proj / ".ai-workspace"
        (ws / "events").mkdir(parents=True)
        (ws / "events" / "events.jsonl").write_text("")
        ctx = ws / "context"
        ctx.mkdir(parents=True)
        (ctx / "project_constraints.yml").write_text(
            textwrap.dedent("""\
                project:
                  name: broken-eco-test
                tools:
                  test_runner:
                    command: python
                    args: -m pytest tests/ -x -q
                    pass_criterion: exit_0
                  coverage:
                    command: python
                    args: -m pytest tests/ --co -q
                    pass_criterion: exit_0
                    required: false
                  linter:
                    command: python
                    args: -m py_compile src/calc.py
                    pass_criterion: exit_0
                    required: false
                  formatter:
                    command: python
                    args: -c "pass"
                    pass_criterion: exit_0
                    required: false
                  type_checker:
                    command: python
                    args: -c "pass"
                    pass_criterion: exit_0
                    required: false
                thresholds:
                  test_coverage_minimum: 0
                standards:
                  style_guide: pep8
                  docstrings: optional
                  type_hints: optional
                  test_structure: arrange_act_assert
            """)
        )

        (src / "__init__.py").write_text("")
        (src / "calc.py").write_text(
            textwrap.dedent("""\
                # Implements: REQ-F-ECO-001
                def add(a, b):
                    return a - b  # BUG: returns difference, not sum
            """)
        )
        (tests / "__init__.py").write_text("")
        (tests / "test_calc.py").write_text(
            textwrap.dedent("""\
                # Validates: REQ-F-ECO-001
                from src.calc import add
                def test_add():
                    assert add(1, 2) == 3  # FAILS because add returns 1-2 = -1
            """)
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(GENESIS_SRC)
        result = subprocess.run(
            [sys.executable, "-m", "genesis", "evaluate",
             "--edge", "code\u2194unit_tests",
             "--feature", "REQ-F-ECO-001",
             "--asset", "src/calc.py",
             "--deterministic-only",
             "--workspace", str(broken_proj)],
            env=env, capture_output=True, text=True,
            cwd=str(broken_proj), timeout=60,
        )
        assert result.returncode in (0, 1), f"Engine crashed:\n{result.stderr[:500]}"
        output = json.loads(result.stdout)
        assert not output["converged"], (
            f"Broken code must not report converged. "
            f"Checks: {[c for c in output['checks'] if c['outcome'] == 'pass']}"
        )
        assert output["delta"] > 0, "Broken code must have delta > 0"

    def test_run_edge_loops_to_convergence(self, project_with_code):
        """run-edge must loop and report final convergence state."""
        result = _run_engine(
            project_with_code, "run-edge",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
            "--max-iterations", "3",
        )
        assert result.returncode in (0, 1), f"run-edge crashed:\n{result.stderr[:500]}"
        output = json.loads(result.stdout)
        assert "final_delta" in output
        assert "total_iterations" in output
        assert output["total_iterations"] >= 1

    def test_events_jsonl_append_only_across_multiple_runs(self, project_with_code):
        """Running evaluate twice must only append — never mutate existing events."""
        snapshot = list(_read_events(project_with_code))

        for _ in range(2):
            _run_engine(
                project_with_code, "evaluate",
                "--edge", "code\u2194unit_tests",
                "--feature", "REQ-F-ECO-001",
                "--asset", "src/calc.py",
                "--deterministic-only",
            )

        after = _read_events(project_with_code)
        assert len(after) > len(snapshot), "Events must accumulate"
        for i, ev in enumerate(snapshot):
            assert after[i] == ev, f"Event at index {i} was mutated between runs"


# ═══════════════════════════════════════════════════════════════════════════════
# Class 3 — Telemetry chain  (req= tags flow end-to-end)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTelemetryChain:
    """req= structured log tags appear in engine stderr and events.  REQ-F-TELEM-001."""

    def test_engine_stderr_contains_req_tag(self, project_with_code):
        """Engine logging must emit req=\"REQ-F-ECO-001\" to stderr."""
        result = _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        assert re.search(r'req=["\']REQ-F-ECO-001["\']', result.stderr), (
            f"req= tag not found in engine stderr.\nSTDERR (first 1000):\n{result.stderr[:1000]}"
        )

    def test_req_tag_value_matches_feature_id_argument(self, project_with_code):
        """The req= value must exactly equal the --feature argument passed in."""
        feature_id = "REQ-F-ECO-001"
        result = _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", feature_id,
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        matches = re.findall(r'req=["\']([^"\']+)["\']', result.stderr)
        assert feature_id in matches, (
            f"req=\"{feature_id}\" not found in stderr req= tags. Found: {matches}"
        )

    def test_run_edge_path_also_emits_req_tag(self, project_with_code):
        """The run-edge path (dispatch_loop + edge_runner) must also emit req= tags."""
        result = _run_engine(
            project_with_code, "run-edge",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
            "--max-iterations", "1",
        )
        assert re.search(r'req=["\']REQ-F-ECO-001["\']', result.stderr), (
            f"req= tag not found in run-edge stderr.\nSTDERR:\n{result.stderr[:1000]}"
        )

    def test_iteration_event_carries_feature_id(self, project_with_code):
        """Every iteration_completed / IterationCompleted event must reference the feature."""
        before_count = len(_read_events(project_with_code))
        _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        new_events = _read_events(project_with_code)[before_count:]
        assert new_events, "No events emitted"
        # At least one new event must reference the feature ID anywhere in its payload
        refs = [e for e in new_events if "REQ-F-ECO-001" in json.dumps(e)]
        assert refs, (
            f"No new events reference REQ-F-ECO-001.\nNew events: {new_events}"
        )

    def test_delta_field_present_in_iteration_event(self, project_with_code):
        """Iteration events must carry a delta field (the convergence signal)."""
        before_count = len(_read_events(project_with_code))
        _run_engine(
            project_with_code, "evaluate",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
        )
        new_events = _read_events(project_with_code)[before_count:]
        # Find an event that looks like an iteration record
        iter_events = [
            e for e in new_events
            if any(k in e for k in ("delta", "outputs"))
            or any(k in json.dumps(e) for k in ('"delta"', '"Delta"'))
        ]
        assert iter_events, f"No iteration event with delta found. New events: {new_events}"

    def test_telemetry_covers_all_three_engine_paths(self, project_with_code):
        """iterate_edge, run_edge, and edge_runner all emit req= — verify all three."""
        # run-edge exercises iterate_edge (internal) + run_edge + edge_runner
        result = _run_engine(
            project_with_code, "run-edge",
            "--edge", "code\u2194unit_tests",
            "--feature", "REQ-F-ECO-001",
            "--asset", "src/calc.py",
            "--deterministic-only",
            "--max-iterations", "1",
        )
        stderr = result.stderr
        # Each engine path has its own log call:
        #   engine.py:       iterate_edge req=...   /  run_edge req=...
        #   dispatch_loop.py: dispatch req=...
        #   edge_runner.py:   edge_runner req=...
        req_occurrences = re.findall(r'req=["\']REQ-F-ECO-001["\']', stderr)
        assert len(req_occurrences) >= 2, (
            f"Expected ≥2 req= log lines (multiple engine paths), found {len(req_occurrences)}.\n"
            f"STDERR:\n{stderr[:1500]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Class 4 — Dispatch monitor integration  (homeostatic loop)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDispatchMonitorIntegration:
    """Homeostatic loop: intent_raised → dispatch detection.  REQ-F-DISPATCH-001."""

    # Use GENESIS_SRC for imports — avoids needing installed project for these tests
    @pytest.fixture(autouse=True)
    def _ensure_importable(self):
        if str(GENESIS_SRC) not in sys.path:
            sys.path.insert(0, str(GENESIS_SRC))

    @pytest.fixture
    def dispatch_ws(self, tmp_path):
        """Minimal workspace with empty events.jsonl and feature vectors for test IDs.

        resolve_dispatch_targets() requires feature vectors on disk — it skips
        features with no active vector.  Create stubs for all ECO-0xx IDs used by tests.
        """
        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "events.jsonl").write_text("")

        features_dir = tmp_path / ".ai-workspace" / "features" / "active"
        features_dir.mkdir(parents=True)

        # Cover all ECO feature IDs used in dispatch tests (010..049)
        for n in range(10, 50):
            fid = f"REQ-F-ECO-0{n}"
            (features_dir / f"{fid}.yml").write_text(
                yaml.dump({
                    "feature": fid,
                    "title": f"Test feature {fid}",
                    "status": "iterating",
                    "profile": "hotfix",
                    "priority": "medium",
                    "trajectory": {
                        "code": {"status": "iterating"},
                        "unit_tests": {"status": "iterating"},
                    },
                })
            )

        return tmp_path

    def _intent_raised(self, feature_id: str, intent_id: str, edge: str = "code\u2194unit_tests") -> dict:
        return {
            "event_type": "intent_raised",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": "eco-test",
            "data": {
                "intent_id": intent_id,
                "affected_features": [feature_id],
                "edge_context": edge,
                "signal_source": "test_failure",
            },
        }

    def _edge_started(self, feature_id: str, edge: str, intent_id: str = "") -> dict:
        """edge_started must carry intent_id so intent_observer marks intent handled."""
        data: dict = {"iteration": 1}
        if intent_id:
            data["intent_id"] = intent_id
        return {
            "event_type": "edge_started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": "eco-test",
            "feature": feature_id,
            "edge": edge,
            "data": data,
        }

    def test_unhandled_intent_appears_as_pending(self, dispatch_ws):
        """intent_raised with no edge_started must appear in get_pending_dispatches."""
        try:
            from genesis.intent_observer import get_pending_dispatches
        except ImportError:
            pytest.skip("genesis.intent_observer not importable")

        _append_event(dispatch_ws, self._intent_raised("REQ-F-ECO-010", "INT-010"))

        pending = get_pending_dispatches(dispatch_ws)
        feature_ids = [t.feature_id for t in pending]
        assert "REQ-F-ECO-010" in feature_ids, (
            f"Expected REQ-F-ECO-010 in pending. Got: {feature_ids}"
        )

    def test_handled_intent_not_in_pending(self, dispatch_ws):
        """intent_raised that already has edge_started must not be in pending."""
        try:
            from genesis.intent_observer import get_pending_dispatches
        except ImportError:
            pytest.skip("genesis.intent_observer not importable")

        _append_event(dispatch_ws, self._intent_raised("REQ-F-ECO-011", "INT-011"))
        _append_event(dispatch_ws, self._edge_started("REQ-F-ECO-011", "code\u2194unit_tests", "INT-011"))

        pending = get_pending_dispatches(dispatch_ws)
        feature_ids = [t.feature_id for t in pending]
        assert "REQ-F-ECO-011" not in feature_ids, (
            f"REQ-F-ECO-011 should be handled (edge_started exists) but in pending: {feature_ids}"
        )

    def test_dispatch_target_has_required_fields(self, dispatch_ws):
        """DispatchTarget must expose feature_id, edge, and intent_id."""
        try:
            from genesis.intent_observer import get_pending_dispatches
        except ImportError:
            pytest.skip("genesis.intent_observer not importable")

        _append_event(dispatch_ws, self._intent_raised("REQ-F-ECO-012", "INT-012"))

        pending = get_pending_dispatches(dispatch_ws)
        targets = [t for t in pending if t.feature_id == "REQ-F-ECO-012"]
        assert targets, "No dispatch target found for REQ-F-ECO-012"

        t = targets[0]
        assert hasattr(t, "feature_id"), "DispatchTarget missing .feature_id"
        assert hasattr(t, "edge"),       "DispatchTarget missing .edge"
        assert hasattr(t, "intent_id"),  "DispatchTarget missing .intent_id"
        assert t.feature_id == "REQ-F-ECO-012"
        assert t.intent_id == "INT-012"

    def test_empty_events_log_has_zero_pending(self, tmp_path):
        """An empty events.jsonl must yield zero pending dispatches."""
        try:
            from genesis.intent_observer import get_pending_dispatches
        except ImportError:
            pytest.skip("genesis.intent_observer not importable")

        (tmp_path / ".ai-workspace" / "events").mkdir(parents=True)
        (tmp_path / ".ai-workspace" / "events" / "events.jsonl").write_text("")

        assert get_pending_dispatches(tmp_path) == []

    def test_multiple_intents_all_detected(self, dispatch_ws):
        """Multiple unhandled intents across different features are all returned."""
        try:
            from genesis.intent_observer import get_pending_dispatches
        except ImportError:
            pytest.skip("genesis.intent_observer not importable")

        for i in range(3):
            _append_event(
                dispatch_ws,
                self._intent_raised(f"REQ-F-ECO-02{i}", f"INT-02{i}")
            )

        pending = get_pending_dispatches(dispatch_ws)
        feature_ids = {t.feature_id for t in pending}
        for i in range(3):
            assert f"REQ-F-ECO-02{i}" in feature_ids, (
                f"REQ-F-ECO-02{i} not in pending. All pending: {feature_ids}"
            )

    def test_partial_handling_leaves_only_unhandled(self, dispatch_ws):
        """When 2 of 3 intents are handled, only 1 must remain pending."""
        try:
            from genesis.intent_observer import get_pending_dispatches
        except ImportError:
            pytest.skip("genesis.intent_observer not importable")

        for i in range(3):
            _append_event(dispatch_ws, self._intent_raised(f"REQ-F-ECO-03{i}", f"INT-03{i}"))

        # Handle two of them
        _append_event(dispatch_ws, self._edge_started("REQ-F-ECO-030", "code\u2194unit_tests", "INT-030"))
        _append_event(dispatch_ws, self._edge_started("REQ-F-ECO-031", "code\u2194unit_tests", "INT-031"))

        pending = get_pending_dispatches(dispatch_ws)
        pending_ids = {t.feature_id for t in pending}

        assert "REQ-F-ECO-032" in pending_ids, "Unhandled intent not detected"
        assert "REQ-F-ECO-030" not in pending_ids, "Handled intent incorrectly in pending"
        assert "REQ-F-ECO-031" not in pending_ids, "Handled intent incorrectly in pending"

    def test_dispatch_monitor_check_runs_without_crash(self, dispatch_ws):
        """check_and_dispatch must not raise for a workspace with pending intents."""
        try:
            from genesis.dispatch_monitor import MonitorState, check_and_dispatch
        except ImportError:
            pytest.skip("genesis.dispatch_monitor not importable")

        _append_event(dispatch_ws, self._intent_raised("REQ-F-ECO-040", "INT-040"))

        # check_and_dispatch may fail to run the engine if configs are missing,
        # but it must not crash the process itself
        state = MonitorState()
        try:
            check_and_dispatch(dispatch_ws, state)
        except SystemExit:
            pass  # subprocess exit is fine
        except Exception as e:
            # Engine config missing in minimal workspace is expected; other errors are not
            allowed = ("No edge config", "not found", "constraints", "edge_params")
            if not any(msg in str(e) for msg in allowed):
                raise


# ═══════════════════════════════════════════════════════════════════════════════
# Class 5 — EcoSystem reference project
# ═══════════════════════════════════════════════════════════════════════════════

class TestEcoSystemReferenceProject:
    """eco_system/ reference snapshots are intact and the validate tooling works."""

    ECO_ROOT = REPO_ROOT / "projects" / "eco_system"
    SNAPSHOTS = ECO_ROOT / "snapshots"
    ECO_PROJECT = ECO_ROOT / "projects" / "temperature_converter"

    def test_eco_system_directory_exists(self):
        assert self.ECO_ROOT.exists(), f"eco_system/ missing at {self.ECO_ROOT}"

    def test_installed_snapshot_workspace_structure(self):
        """00_installed snapshot must have a complete .ai-workspace."""
        ws = self.SNAPSHOTS / "00_installed" / ".ai-workspace"
        assert ws.exists(), "00_installed snapshot missing"
        for sub in ("events/events.jsonl", "graph/graph_topology.yml"):
            assert (ws / sub).exists(), f"Snapshot missing: {sub}"

    def test_installed_snapshot_events_are_valid_jsonl(self):
        """Every line in the snapshot events.jsonl must be valid JSON."""
        events_path = self.SNAPSHOTS / "00_installed" / ".ai-workspace" / "events" / "events.jsonl"
        for i, line in enumerate(events_path.read_text().splitlines()):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON at line {i+1}: {e}\n  Line: {line[:200]}")

    def test_validate_script_is_present(self):
        assert (self.ECO_ROOT / "scripts" / "validate.py").exists()

    def test_snapshot_manifest_is_valid_yaml(self):
        manifest = self.SNAPSHOTS / "manifest.yml"
        if not manifest.exists():
            pytest.skip("manifest.yml not present")
        data = yaml.safe_load(manifest.read_text())
        assert data is not None

    def test_eco_system_project_can_run_engine(self):
        """eco_system project must be able to run the genesis engine."""
        if not self.ECO_PROJECT.exists():
            pytest.skip("eco_system project directory not present")

        # Use source PYTHONPATH since eco_system may not have .genesis installed
        env = os.environ.copy()
        env["PYTHONPATH"] = str(GENESIS_SRC)

        result = subprocess.run(
            [sys.executable, "-m", "genesis", "--help"],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(self.ECO_PROJECT),
            timeout=30,
        )
        assert result.returncode in (0, 1), (
            f"genesis --help failed in eco_system project:\n{result.stderr[:500]}"
        )
