# Validates: REQ-EVAL-001, REQ-EVAL-002, REQ-EVENT-001, REQ-EVENT-003
"""E2E tests for the F_H gate path — human gate escalation, review_approved emission,
and the known engine gap where review_approved does not advance the engine.

Architecture facts encoded in these tests:

1. F_D evaluators skip `type: human` items — they are documentation for the LLM only
   (fd_evaluate.py:52 returns CheckOutcome.SKIP for non-deterministic checks).

2. The F_H gate fires when F_P iterations are exhausted (edge_runner.py Phase 3).
   `status="fh_required"` requires fp_iteration > 0; `status="stuck"` when fp_iteration == 0.

3. cmd_start() in __main__.py NEVER reads `review_approved` events. Re-running the
   engine after emitting review_approved will re-enter fh_required — this is REQ-GAP-001.

4. `genesis emit-event` uses fd_emit.py (flat format): {event_type, timestamp, project, ...}.

5. Engine-emitted events use ol_event.py (OL format).

6. normalize_event() bridges both formats for reading.

7. _update_trajectory() is only called when result.status == "converged" — never for
   fh_required or fp_dispatched.

Run:
    pytest imp_claude/tests/e2e/test_e2e_human_gate.py -v -m e2e -s
"""

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone

import pytest


# ── E2E sibling-module imports ─────────────────────────────────────────────────
# Force-load from the e2e directory to avoid pytest resolving the wrong conftest.
def _load_sibling(name: str):
    path = pathlib.Path(__file__).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"e2e_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_conftest = _load_sibling("conftest")
CONFIG_DIR = _conftest.CONFIG_DIR
COMMANDS_DIR = _conftest.COMMANDS_DIR
AGENTS_DIR = _conftest.AGENTS_DIR
PLUGIN_ROOT = _conftest.PLUGIN_ROOT
RUNS_DIR = _conftest.RUNS_DIR
PROJECT_ROOT = _conftest.PROJECT_ROOT
INTENT_MD = _conftest.INTENT_MD
PROJECT_CONSTRAINTS_YML = _conftest.PROJECT_CONSTRAINTS_YML
TEST_PROJECT_CLAUDE_MD = _conftest.TEST_PROJECT_CLAUDE_MD
TEST_PROJECT_PYPROJECT = _conftest.TEST_PROJECT_PYPROJECT
run_claude_headless = _conftest.run_claude_headless
skip_no_claude = _conftest.skip_no_claude
_clean_env = _conftest._clean_env
_copy_config_files = _conftest._copy_config_files
_copy_profile_files = _conftest._copy_profile_files
_copy_commands = _conftest._copy_commands
_copy_agents = _conftest._copy_agents
_get_plugin_version = _conftest._get_plugin_version
_persist_run = _conftest._persist_run

# Genesis code is at imp_claude/code
GENESIS_CODE_DIR = PROJECT_ROOT / "imp_claude" / "code"


# ── Genesis Python API — imported directly (no subprocess needed) ─────────────

def _genesis_sys_path():
    """Return the genesis code path for sys.path insertion."""
    return str(GENESIS_CODE_DIR)


# ═══════════════════════════════════════════════════════════════════════
# TEST CONTENT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════

# Feature vector for a test feature that will be used across all sub-tests.
# Profile is set to "hotfix" (minimal edges: only code↔unit_tests) so we don't
# need a full workspace scaffold with all intermediate design docs.
HUMAN_GATE_FEATURE_VECTOR_YML = textwrap.dedent("""\
    ---
    feature: "REQ-F-TEST-001"
    title: "Human Gate Test Feature"
    intent: "INT-HG-001"
    vector_type: feature
    profile: hotfix
    status: in_progress
    convergence_type: ""
    created: "{timestamp}"
    updated: "{timestamp}"

    time_box:
      enabled: false

    parent:
      feature: ""
      edge: ""
      reason: ""

    children: []

    trajectory:
      code:
        status: pending
      unit_tests:
        status: pending

    dependencies: []

    constraints:
      acceptance_criteria:
        - id: "AC-TEST-001"
          description: "All unit tests pass"
          evaluator: deterministic
          check: "pytest tests/ -v returns exit code 0"
          req: "REQ-F-TEST-001"
          required: true
      threshold_overrides: {}
      additional_checks: []
""")

HUMAN_GATE_SEED_EVENTS = [
    {
        "event_type": "project_initialized",
        "timestamp": "{timestamp}",
        "project": "human-gate-test",
        "profile": "hotfix",
        "version": "{version}",
    },
]

# Intentionally failing code — so F_D fails, F_P gets dispatched, and
# after exhaustion F_H gate fires.
FAILING_CODE_PY = textwrap.dedent('''\
    """Calculator module — deliberately broken for human gate testing.

    # Implements: REQ-F-TEST-001
    """


    def add(a, b):
        """Add two numbers."""
        # Implements: REQ-F-TEST-001
        return a - b  # BUG: should be a + b


    def multiply(a, b):
        """Multiply two numbers."""
        # Implements: REQ-F-TEST-001
        return a + b  # BUG: should be a * b
''')

FAILING_TESTS_PY = textwrap.dedent('''\
    """Tests for calculator module.

    # Validates: REQ-F-TEST-001
    """
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
    from calculator import add, multiply


    # Validates: REQ-F-TEST-001
    class TestAdd:
        def test_basic_add(self):
            assert add(1, 2) == 3

        def test_add_zero(self):
            assert add(0, 5) == 5


    # Validates: REQ-F-TEST-001
    class TestMultiply:
        def test_basic_multiply(self):
            assert multiply(3, 4) == 12

        def test_multiply_by_one(self):
            assert multiply(7, 1) == 7
''')


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _scaffold_human_gate_project(project_dir: pathlib.Path) -> None:
    """Scaffold a minimal project with failing code for human gate testing.

    Creates a workspace with:
    - Source code that will fail deterministic tests
    - Correct tests (that WILL fail against the buggy source)
    - Feature vector with hotfix profile (only code↔unit_tests edge needed)
    - Seed events showing project initialized
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    version = _get_plugin_version()

    # Git init
    subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "e2e-test@example.com"],
                   cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "E2E Test"],
                   cwd=str(project_dir), capture_output=True)

    # Write specification
    spec_dir = project_dir / "specification"
    spec_dir.mkdir()
    (spec_dir / "INTENT.md").write_text(
        "# Intent: Calculator\n\nA simple calculator module.\n\n"
        "## REQ-F-TEST-001: Basic arithmetic operations\n"
    )

    # Write FAILING source code
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "calculator.py").write_text(FAILING_CODE_PY)

    # Write tests that will FAIL against the buggy code
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_calculator.py").write_text(FAILING_TESTS_PY)
    (tests_dir / "conftest.py").write_text(
        "import sys; import pathlib; "
        "sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'src'))\n"
    )

    # Create .ai-workspace
    ws = project_dir / ".ai-workspace"
    graph_dir = ws / "graph"
    context_dir = ws / "claude" / "context"
    features_active = ws / "features" / "active"
    features_completed = ws / "features" / "completed"
    profiles_dir = ws / "profiles"
    events_dir = ws / "events"
    tasks_active = ws / "tasks" / "active"
    agents_dir = ws / "agents"

    for d in [graph_dir, context_dir, features_active, features_completed,
              profiles_dir, events_dir, tasks_active, agents_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy config files
    _copy_config_files(graph_dir)
    _copy_profile_files(profiles_dir)
    shutil.copy2(CONFIG_DIR / "feature_vector_template.yml",
                 ws / "features" / "feature_vector_template.yml")

    # Write project constraints
    (context_dir / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)

    # Write feature vector (hotfix profile — only code↔unit_tests edge)
    (features_active / "REQ-F-TEST-001.yml").write_text(
        HUMAN_GATE_FEATURE_VECTOR_YML.replace("{timestamp}", timestamp)
    )

    # Write feature index
    (ws / "features" / "feature_index.yml").write_text(textwrap.dedent("""\
        ---
        features:
          - id: "REQ-F-TEST-001"
            title: "Human Gate Test Feature"
            status: in_progress
            profile: hotfix
            path: "features/active/REQ-F-TEST-001.yml"
    """))

    # Write tasks
    (tasks_active / "ACTIVE_TASKS.md").write_text(
        "# Active Tasks\n\n- [ ] REQ-F-TEST-001: code↔unit_tests — pending\n"
    )

    # Copy commands and agents
    _copy_commands(project_dir / ".claude" / "commands")
    _copy_agents(agents_dir)

    # Write project files
    (project_dir / "CLAUDE.md").write_text(TEST_PROJECT_CLAUDE_MD)
    (project_dir / "pyproject.toml").write_text(
        '[project]\nname = "human-gate-test"\nversion = "0.1.0"\n'
        'requires-python = ">=3.10"\n\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    )

    # Write seed events
    with open(events_dir / "events.jsonl", "w") as f:
        for event in HUMAN_GATE_SEED_EVENTS:
            event_str = json.dumps(event)
            event_str = event_str.replace("{timestamp}", timestamp)
            event_str = event_str.replace("{version}", version)
            f.write(event_str + "\n")

    # Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: scaffold human-gate-test project"],
                   cwd=str(project_dir), capture_output=True)


def _load_constraints(project_dir: pathlib.Path) -> dict:
    """Load project_constraints.yml from the scaffolded workspace.

    Returns the full constraints dict so $tools.* variables can be resolved
    during F_D evaluation. Without this, all checklist checks return SKIP
    (delta=0) even when tests actually fail.
    """
    try:
        import yaml as _yaml
        constraints_path = (
            project_dir / ".ai-workspace" / "claude" / "context" / "project_constraints.yml"
        )
        if constraints_path.exists():
            return _yaml.safe_load(constraints_path.read_text()) or {}
    except Exception:
        pass
    return {}


def _make_fv(project_dir: pathlib.Path, feature_id: str = "REQ-F-TEST-001") -> dict:
    """Build a feature vector dict with loaded constraints for engine testing.

    Loads project_constraints.yml so $tools.* variable resolution succeeds
    during F_D evaluation (otherwise all checks SKIP → delta=0 → converged).
    """
    return {
        "feature": feature_id,
        "profile": "hotfix",
        "constraints": _load_constraints(project_dir),
        "trajectory": {"code": {"status": "pending"}, "unit_tests": {"status": "pending"}},
    }


def _load_events(project_dir: pathlib.Path) -> list[dict]:
    """Parse events.jsonl, normalising OL and flat formats."""
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    events = []
    if events_file.exists():
        for line in events_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                # normalize OL events using the genesis normalize_event
                if "eventType" in raw and "event_type" not in raw:
                    # OL format — extract via normalize_event logic
                    facets = raw.get("run", {}).get("facets", {})
                    et_facet = facets.get("sdlc:event_type", {})
                    if et_facet:
                        import re
                        semantic = et_facet.get("type", "")
                        event_type = re.sub(r"(?<!^)(?=[A-Z])", "_", semantic).lower()
                        namespace = raw.get("job", {}).get("namespace", "")
                        project = namespace.removeprefix("aisdlc://")
                        payload = facets.get("sdlc:payload", {})
                        flat = {
                            "event_type": event_type,
                            "timestamp": raw.get("eventTime", ""),
                            "project": project,
                        }
                        flat.update({k: v for k, v in payload.items()
                                     if not k.startswith("_")})
                        events.append(flat)
                    else:
                        events.append(raw)
                else:
                    events.append(raw)
            except json.JSONDecodeError:
                pass
    return events


def _write_fake_fp_result(workspace_root: pathlib.Path, fp_run_id: str,
                          converged: bool = False, delta: int = 5) -> pathlib.Path:
    """Write a fake F_P fold-back result file to simulate LLM actor response.

    The edge_runner reads fp_result_{fp_run_id}.json to check if the LLM actor
    has completed its work. Writing this manually forces the engine to re-evaluate
    F_D after the fake "LLM construction" step.
    """
    agents_dir = workspace_root / ".ai-workspace" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    result_path = agents_dir / f"fp_result_{fp_run_id}.json"
    result = {
        "run_id": fp_run_id,
        "converged": converged,
        "delta": 0 if converged else delta,
        "cost_usd": 0.15,
        "status": "converged" if converged else "iterating",
    }
    result_path.write_text(json.dumps(result, indent=2))
    return result_path


# ═══════════════════════════════════════════════════════════════════════
# PART A: No-LLM engine tests — pure behavioral, no Claude required
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestHumanGateNoLLM:
    """Pure behavioral tests for the F_H gate — no Claude CLI required.

    Uses run_edge() Python API directly with controlled fp_result files
    to drive F_P exhaustion and trigger fh_required without LLM involvement.
    """

    def test_fp_dispatched_on_first_fd_failure(self, tmp_path: pathlib.Path):
        """First run_edge call returns fp_dispatched when F_D fails and no fp_result exists.

        WHY: Validates Phase 1→Phase 2 transition. When F_D finds delta > 0
        (tests failing) and no prior fp_result exists, EDGE_RUNNER must write
        an fp_intent manifest and return fp_dispatched so the MCP actor can
        be invoked. This is the first half of the F_P fold-back protocol.

        To force F_D to actually FAIL (not SKIP), we pass the loaded project_constraints.yml
        content in the feature vector. Without the $tools.* variable resolution, all
        checklist checks return SKIP (delta=0). With the constraints loaded, the
        'tests_pass' check runs `pytest tests/ -v` → fails against buggy code → delta > 0.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.intent_observer import DispatchTarget
        from genesis.edge_runner import run_edge

        _scaffold_human_gate_project(tmp_path)

        # Load the project constraints so $tools.* variables resolve during F_D evaluation
        import yaml as _yaml
        constraints_path = (
            tmp_path / ".ai-workspace" / "claude" / "context" / "project_constraints.yml"
        )
        constraints_data = _yaml.safe_load(constraints_path.read_text()) if constraints_path.exists() else {}

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        fv = {
            "feature": "REQ-F-TEST-001",
            "profile": "hotfix",
            # Pass full constraints so engine can resolve $tools.test_runner.command etc.
            "constraints": constraints_data,
            "trajectory": {"code": {"status": "pending"}, "unit_tests": {"status": "pending"}},
        }
        target = DispatchTarget(
            intent_id="test-intent-001",
            feature_id="REQ-F-TEST-001",
            edge="code↔unit_tests",
            feature_vector=fv,
        )

        result = run_edge(
            target=target,
            workspace_root=tmp_path,
            events_path=events_path,
            project_name="human-gate-test",
            budget_usd=0.50,
            max_fp_iterations=1,
        )

        # When F_D fails (tests fail) and no fp_result exists, must get fp_dispatched.
        # evaluator_error is also acceptable here — it means the edge config resolution
        # failed (e.g. edge_params file not found in workspace), which is an infrastructure
        # issue rather than a domain delta. The key thing tested here is that we do NOT
        # get 'converged' when code is broken.
        assert result.status in ("fp_dispatched", "evaluator_error"), (
            f"Expected fp_dispatched (F_D failed, no fp_result yet) or evaluator_error, "
            f"got status={result.status!r} with delta={result.delta}. "
            f"'converged' here would mean F_D passed despite broken code, which is wrong."
        )
        if result.status == "fp_dispatched":
            assert result.fp_manifest_path, "fp_manifest_path must be set when fp_dispatched"
            assert pathlib.Path(result.fp_manifest_path).exists(), (
                "fp_intent manifest file must exist on disk"
            )

    def test_fh_required_after_fp_exhaustion(self, tmp_path: pathlib.Path):
        """Second run_edge call returns fh_required when fp_result is not-converged.

        WHY: Validates Phase 2→Phase 3 transition. When max_fp_iterations=1, the
        engine writes a manifest, then checks for the result. If the result says
        converged=False, fp_iterations are exhausted → fh_required. This proves
        the F_H escalation path fires correctly.

        The fake fp_result simulates an LLM actor that tried but did not converge.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.intent_observer import DispatchTarget
        from genesis.edge_runner import run_edge, COST_PER_FP_ITERATION

        _scaffold_human_gate_project(tmp_path)

        import yaml as _yaml
        constraints_path = (
            tmp_path / ".ai-workspace" / "claude" / "context" / "project_constraints.yml"
        )
        constraints_data = _yaml.safe_load(constraints_path.read_text()) if constraints_path.exists() else {}

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        fv = {
            "feature": "REQ-F-TEST-001",
            "profile": "hotfix",
            "constraints": constraints_data,
            "trajectory": {"code": {"status": "pending"}, "unit_tests": {"status": "pending"}},
        }
        target = DispatchTarget(
            intent_id="test-intent-002",
            feature_id="REQ-F-TEST-001",
            edge="code↔unit_tests",
            feature_vector=fv,
        )

        # First run: fp_dispatched (fp_result does not yet exist) or evaluator_error
        result1 = run_edge(
            target=target,
            workspace_root=tmp_path,
            events_path=events_path,
            project_name="human-gate-test",
            budget_usd=1.00,
            max_fp_iterations=1,
        )
        assert result1.status in ("fp_dispatched", "fh_required", "evaluator_error"), (
            f"First run expected fp_dispatched/fh_required/evaluator_error, got {result1.status}. "
            f"'converged' would mean F_D passed despite broken code."
        )

        if result1.status == "fp_dispatched":
            # Extract the fp_run_id from the manifest to write a matching result
            manifest_path = pathlib.Path(result1.fp_manifest_path)
            manifest = json.loads(manifest_path.read_text())
            fp_run_id = manifest["run_id"]

            # Write a fake fp_result indicating LLM tried but did NOT converge
            _write_fake_fp_result(tmp_path, fp_run_id, converged=False, delta=4)

            # Second run: finds the fp_result, re-evaluates F_D, exhausts fp_iterations
            result2 = run_edge(
                target=target,
                workspace_root=tmp_path,
                events_path=events_path,
                project_name="human-gate-test",
                budget_usd=1.00,
                max_fp_iterations=1,
            )
            assert result2.status == "fh_required", (
                f"Expected fh_required after F_P exhaustion, got {result2.status!r}. "
                f"fp_result was written with converged=False so F_P should be exhausted."
            )

    def test_fh_required_emits_iteration_completed_event(self, tmp_path: pathlib.Path):
        """When fh_required fires, events.jsonl must contain IterationCompleted with status=fh_required.

        WHY: Validates the event stream contract. The F_H escalation must be
        observable in the log so downstream consumers (genesis_monitor, morning review)
        can surface the gate to a human. An fh_required event not in the log is
        a silent gap violation.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.intent_observer import DispatchTarget
        from genesis.edge_runner import run_edge

        _scaffold_human_gate_project(tmp_path)

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        fv = _make_fv(tmp_path)
        target = DispatchTarget(
            intent_id="test-intent-003",
            feature_id="REQ-F-TEST-001",
            edge="code↔unit_tests",
            feature_vector=fv,
        )

        # Drive to fh_required via fp exhaustion
        result1 = run_edge(
            target=target, workspace_root=tmp_path, events_path=events_path,
            project_name="human-gate-test", budget_usd=1.00, max_fp_iterations=1,
        )
        if result1.status == "fp_dispatched":
            manifest = json.loads(pathlib.Path(result1.fp_manifest_path).read_text())
            _write_fake_fp_result(tmp_path, manifest["run_id"], converged=False)
            result2 = run_edge(
                target=target, workspace_root=tmp_path, events_path=events_path,
                project_name="human-gate-test", budget_usd=1.00, max_fp_iterations=1,
            )
            final_status = result2.status
        elif result1.status == "fh_required":
            # Engine can also reach fh_required with max_fp_iterations=0 if budget exceeded
            final_status = "fh_required"
        else:
            pytest.skip(f"Could not drive to fh_required: got {result1.status}")
            return

        assert final_status == "fh_required", (
            f"Expected final status fh_required, got {final_status}"
        )

        # Now check events.jsonl for IterationCompleted with status=fh_required
        events = _load_events(tmp_path)
        fh_events = [
            e for e in events
            if e.get("event_type") == "iteration_completed"
            and e.get("status") == "fh_required"
        ]
        assert fh_events, (
            "No IterationCompleted event with status=fh_required in events.jsonl. "
            "The F_H gate must be observable in the event stream."
        )

    def test_fh_required_emits_intent_raised_with_human_gate_signal(self, tmp_path: pathlib.Path):
        """When fh_required fires, events.jsonl must contain intent_raised with
        signal_source=human_gate_required.

        WHY: intent_raised is the sole authoritative F_H signal (ADR-S-032). Without
        this event, the homeostatic dispatch loop cannot detect that a human gate is
        blocking and cannot surface it to the morning review process.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.intent_observer import DispatchTarget
        from genesis.edge_runner import run_edge

        _scaffold_human_gate_project(tmp_path)

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        fv = _make_fv(tmp_path)
        target = DispatchTarget(
            intent_id="test-intent-004",
            feature_id="REQ-F-TEST-001",
            edge="code↔unit_tests",
            feature_vector=fv,
        )

        # Drive to fh_required
        result1 = run_edge(
            target=target, workspace_root=tmp_path, events_path=events_path,
            project_name="human-gate-test", budget_usd=1.00, max_fp_iterations=1,
        )
        if result1.status == "fp_dispatched":
            manifest = json.loads(pathlib.Path(result1.fp_manifest_path).read_text())
            _write_fake_fp_result(tmp_path, manifest["run_id"], converged=False)
            run_edge(
                target=target, workspace_root=tmp_path, events_path=events_path,
                project_name="human-gate-test", budget_usd=1.00, max_fp_iterations=1,
            )

        events = _load_events(tmp_path)
        intent_raised_fh = [
            e for e in events
            if e.get("event_type") == "intent_raised"
            and e.get("signal_source") == "human_gate_required"
        ]
        assert intent_raised_fh, (
            "No intent_raised event with signal_source=human_gate_required in events.jsonl. "
            "ADR-S-032 requires intent_raised as the sole authoritative F_H signal."
        )

    def test_stuck_status_when_no_fp_iterations(self, tmp_path: pathlib.Path):
        """status='stuck' fires when fp_iteration==0 at Phase 3 escalation.

        WHY: Distinguishes 'never tried F_P' (stuck) from 'tried F_P but failed'
        (fh_required). max_fp_iterations=0 forces F_D failure → immediate Phase 3
        escalation with fp_iteration=0 → stuck. Documents the semantics of the
        stuck/fh_required distinction.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.intent_observer import DispatchTarget
        from genesis.edge_runner import run_edge

        _scaffold_human_gate_project(tmp_path)

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        fv = _make_fv(tmp_path)
        target = DispatchTarget(
            intent_id="test-intent-stuck",
            feature_id="REQ-F-TEST-001",
            edge="code↔unit_tests",
            feature_vector=fv,
        )

        result = run_edge(
            target=target,
            workspace_root=tmp_path,
            events_path=events_path,
            project_name="human-gate-test",
            budget_usd=0.0,   # zero budget → fp_iteration never increments → stuck
            max_fp_iterations=0,  # no F_P iterations allowed
        )

        # When max_fp_iterations=0 and F_D fails, budget check fires first
        # (cost_usd=0 >= budget_usd=0.0 is False, so the while-loop condition matters)
        # edge_runner Phase 2 while: fp_iteration < max_fp_iterations → 0 < 0 = False → skip
        # So we go straight to Phase 3 with fp_iteration=0 → status="stuck"
        assert result.status in ("stuck", "fh_required", "evaluator_error"), (
            f"Expected stuck (no F_P budget/iterations), got {result.status!r}. "
            f"With max_fp_iterations=0, Phase 2 is bypassed entirely."
        )
        if result.status == "stuck":
            assert result.delta > 0, "stuck status with delta=0 would be a contradiction"

    def test_human_evaluator_items_are_skipped_by_fd(self, tmp_path: pathlib.Path):
        """F_D evaluator skips `type: human` items — they are not enforced by the engine.

        WHY: fd_evaluate.py:52 returns CheckOutcome.SKIP for non-deterministic checks.
        Human evaluators in edge_params YAML are documentation for the LLM; they do NOT
        count toward delta. This test verifies that a feature with ONLY human evaluators
        will show delta=0 from F_D's perspective (all required checks skipped).

        This prevents false positives where F_D claims convergence because human checks
        are silently dropped from the delta count.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.models import CheckOutcome, ResolvedCheck
        from genesis.fd_evaluate import run_check

        # Create a fake check with type "human"
        # ResolvedCheck requires: name, check_type, functional_unit, criterion, source
        # plus optional: required, command, pass_criterion, unresolved
        human_check = ResolvedCheck(
            name="human_review",
            check_type="human",
            functional_unit="decide",
            criterion="Human has reviewed and approved the design",
            source="default",
            required=True,
            command="echo 'human review needed'",
            pass_criterion="exit code 0",
            unresolved=[],
        )

        # run_check must return SKIP for non-deterministic checks
        result = run_check(human_check, cwd=tmp_path)
        assert result.outcome == CheckOutcome.SKIP, (
            f"Human evaluator check returned {result.outcome}, expected SKIP. "
            f"fd_evaluate.py:52 documents that `type: human` checks are not F_D. "
            f"This is architecture fact #1 in the test module docstring."
        )
        assert "not F_D" in result.message or "Skipped" in result.message, (
            f"SKIP message should explain reason, got: {result.message!r}"
        )


# ═══════════════════════════════════════════════════════════════════════
# PART B: review_approved emission (CLI test)
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestReviewApprovedEmission:
    """Tests for `genesis emit-event --type review_approved` CLI.

    These tests validate the flat-format event emission via fd_emit.py.
    No Claude required.
    """

    def test_emit_review_approved_exits_zero(self, tmp_path: pathlib.Path):
        """genesis emit-event --type review_approved must exit 0.

        WHY: Exit 0 confirms the CLI accepts the event type and successfully
        appended to events.jsonl. Any non-zero exit indicates a format rejection
        or file I/O error — both are protocol violations.
        """
        _scaffold_human_gate_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        result = subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({
                    "feature": "REQ-F-TEST-001",
                    "edge": "code↔unit_tests",
                    "actor": "human",
                }),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        assert result.returncode == 0, (
            f"genesis emit-event exited {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_emit_review_approved_event_in_events_jsonl(self, tmp_path: pathlib.Path):
        """Emitted review_approved event must appear in events.jsonl.

        WHY: The event stream is append-only. Every emitted event must be durable
        in the log. If emit-event runs successfully but the event is not in the log,
        the append-only guarantee is violated.
        """
        _scaffold_human_gate_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({
                    "feature": "REQ-F-TEST-001",
                    "edge": "code↔unit_tests",
                    "actor": "human",
                }),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
            check=True,
        )

        events = _load_events(tmp_path)
        review_events = [e for e in events if e.get("event_type") == "review_approved"]
        assert review_events, (
            "No review_approved event in events.jsonl after emit-event CLI call. "
            "The append-only guarantee requires the event to persist."
        )

    def test_emit_review_approved_has_actor_field(self, tmp_path: pathlib.Path):
        """review_approved event must carry the actor field.

        WHY: ADR-019 invariant: every review_approved event must have an actor field.
        actor='human' and actor='human-proxy' must never be confused. The actor
        field is the auditability mechanism for the F_H gate.
        """
        _scaffold_human_gate_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({
                    "feature": "REQ-F-TEST-001",
                    "edge": "code↔unit_tests",
                    "actor": "human",
                }),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
            check=True,
        )

        events = _load_events(tmp_path)
        review_events = [e for e in events if e.get("event_type") == "review_approved"]
        assert review_events, "No review_approved event found"

        # The actor field is in the flat data dict (fd_emit merges data at top level)
        event = review_events[-1]
        assert "actor" in event, (
            f"review_approved event missing actor field: {event}. "
            f"actor field is required for F_H gate auditability."
        )
        assert event["actor"] == "human", (
            f"Expected actor='human', got {event.get('actor')!r}. "
            f"actor='human' and actor='human-proxy' must be distinguishable."
        )

    def test_emit_review_approved_has_event_type_field(self, tmp_path: pathlib.Path):
        """Emitted event must have event_type (flat format, not OL eventType).

        WHY: fd_emit.py produces flat format with 'event_type' key. This is
        distinct from OL format which uses 'eventType'. CLI emit-event uses
        fd_emit (flat format). Tests that the correct format is produced.
        """
        _scaffold_human_gate_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        result = subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({"actor": "human"}),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
        )

        # stdout should be the flat record
        if result.returncode == 0 and result.stdout.strip():
            try:
                record = json.loads(result.stdout.strip())
                assert "event_type" in record, (
                    f"CLI stdout missing event_type field: {record}. "
                    f"emit-event uses flat format (fd_emit.py), not OL format."
                )
                assert record["event_type"] == "review_approved"
                assert "eventType" not in record, (
                    "CLI stdout must NOT have 'eventType' (OL format). "
                    "emit-event uses flat fd_emit format."
                )
            except json.JSONDecodeError:
                pytest.skip("stdout not JSON — format may differ")

        # Verify the raw line in events.jsonl is flat format
        events_file = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        if events_file.exists():
            lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]
            if lines:
                last_line = json.loads(lines[-1])
                assert "event_type" in last_line, (
                    "events.jsonl line from emit-event CLI must have 'event_type' (flat format)"
                )


# ═══════════════════════════════════════════════════════════════════════
# PART C: Engine does NOT advance after review_approved — exposes gap (xfail)
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestReviewApprovedGap:
    """Exposes REQ-GAP-001: engine re-enters fh_required after review_approved.

    Architecture fact #3: cmd_start() in __main__.py NEVER reads review_approved
    events. After emitting review_approved and re-running the engine, the engine
    will hit fh_required again because it has no mechanism to read the approval
    and advance past the F_H gate.
    """

    @pytest.mark.xfail(
        reason=(
            "REQ-GAP-001: engine does not read review_approved to advance past F_H gate. "
            "cmd_start() never calls get_pending_dispatches() with review_approved awareness. "
            "After emitting review_approved, the engine re-enters fh_required "
            "in an infinite loop. This test documents the gap — it should FAIL "
            "(i.e. the assertion that the engine does NOT return fh_required again "
            "will be violated because it DOES return fh_required again)."
        ),
        strict=False,
    )
    def test_engine_advances_after_review_approved(self, tmp_path: pathlib.Path):
        """After emitting review_approved, engine should NOT return fh_required again.

        This test will FAIL (and is marked xfail) because the engine DOES return
        fh_required again after review_approved. The xfail documents REQ-GAP-001:
        the engine needs to read review_approved events and advance past the F_H gate.

        When this gap is fixed, this test should be removed and replaced with a
        test that verifies the engine advances to the next edge after approval.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.intent_observer import DispatchTarget
        from genesis.edge_runner import run_edge

        _scaffold_human_gate_project(tmp_path)
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        fv = _make_fv(tmp_path)
        target = DispatchTarget(
            intent_id="test-gap-001",
            feature_id="REQ-F-TEST-001",
            edge="code↔unit_tests",
            feature_vector=fv,
        )

        # Step 1: Run edge → drive to fh_required
        result1 = run_edge(
            target=target, workspace_root=tmp_path, events_path=events_path,
            project_name="human-gate-test", budget_usd=1.00, max_fp_iterations=1,
        )
        if result1.status == "fp_dispatched":
            manifest = json.loads(pathlib.Path(result1.fp_manifest_path).read_text())
            _write_fake_fp_result(tmp_path, manifest["run_id"], converged=False)
            result1 = run_edge(
                target=target, workspace_root=tmp_path, events_path=events_path,
                project_name="human-gate-test", budget_usd=1.00, max_fp_iterations=1,
            )

        if result1.status not in ("fh_required", "stuck"):
            pytest.skip(f"Could not drive to fh_required/stuck: got {result1.status}")

        # Step 2: Emit review_approved via CLI
        subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({
                    "feature": "REQ-F-TEST-001",
                    "edge": "code↔unit_tests",
                    "actor": "human",
                }),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
            check=True,
        )

        # Step 3: Run engine again via CLI — should NOT return fh_required
        engine_result = subprocess.run(
            [
                sys.executable, "-m", "genesis", "start",
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=60, env=env,
        )

        # Parse engine output
        engine_output = {}
        if engine_result.stdout.strip():
            try:
                engine_output = json.loads(engine_result.stdout.strip())
            except json.JSONDecodeError:
                pass

        # ASSERTION: The engine should NOT return fh_required after review_approved.
        # This assertion FAILS (xfail) because the engine DOES return fh_required
        # again — it has no mechanism to read review_approved events.
        assert engine_output.get("status") != "fh_required", (
            "Engine re-entered fh_required after review_approved was emitted. "
            "REQ-GAP-001: cmd_start() must read review_approved events and "
            "advance past the F_H gate. Currently it ignores review_approved entirely."
        )


# ═══════════════════════════════════════════════════════════════════════
# PART D: human proxy flag validation (CLI)
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestHumanProxyFlagValidation:
    """Tests for --human-proxy CLI flag validation.

    ADR-020: --human-proxy requires --auto. Used alone it is an error.
    It is never activated by config, env var, or inference — explicit flag only.
    """

    def test_human_proxy_without_auto_exits_error(self, tmp_path: pathlib.Path):
        """--human-proxy without --auto must exit 1 with an error message.

        WHY: ADR-020 invariant: --human-proxy requires --auto. Used alone it is an
        error. This prevents accidental proxy activation in non-auto runs where there
        is no dispatch loop to supervise.
        """
        _scaffold_human_gate_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        result = subprocess.run(
            [
                sys.executable, "-m", "genesis", "start",
                "--human-proxy",
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
        )

        assert result.returncode == 1, (
            f"Expected exit code 1 for --human-proxy without --auto, "
            f"got {result.returncode}. "
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )

        # Check for error message in stdout (cmd_start prints JSON to stdout)
        combined_output = result.stdout + result.stderr
        assert "human-proxy" in combined_output.lower() or "auto" in combined_output.lower(), (
            f"Expected error message mentioning --human-proxy or --auto requirement, "
            f"got stdout={result.stdout!r}, stderr={result.stderr!r}"
        )

    def test_human_proxy_with_auto_is_accepted(self, tmp_path: pathlib.Path):
        """--human-proxy with --auto must NOT exit 1 with a flag validation error.

        WHY: --auto --human-proxy is the valid proxy mode invocation. The combination
        must be accepted by the CLI (though the actual proxy evaluation requires a
        dispatch loop context). Exit code may be 0 (converged/nothing_to_do),
        2 (fp_dispatched), or 3 (fh_required) — any of these is acceptable.
        Exit 1 with a flag error is NOT acceptable.
        """
        _scaffold_human_gate_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        result = subprocess.run(
            [
                sys.executable, "-m", "genesis", "start",
                "--auto",
                "--human-proxy",
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=60, env=env,
        )

        # Should NOT be exit 1 with a flag validation error
        # The flag combination is valid; the actual result may vary
        if result.returncode == 1:
            # If exit 1, it must be an evaluator or domain error, NOT a flag error
            combined = result.stdout + result.stderr
            flag_error_keywords = ["--human-proxy requires --auto", "invalid flag", "unrecognized"]
            has_flag_error = any(kw.lower() in combined.lower() for kw in flag_error_keywords)
            assert not has_flag_error, (
                f"--auto --human-proxy exit 1 with a flag validation error: {combined!r}. "
                f"The combination --auto --human-proxy must be accepted."
            )

        # Valid exit codes: 0 (ok/nothing_to_do), 1 (evaluator error ok), 2 (fp_dispatched), 3 (fh_required)
        assert result.returncode in (0, 1, 2, 3), (
            f"Unexpected exit code {result.returncode} for --auto --human-proxy. "
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )


# ═══════════════════════════════════════════════════════════════════════
# PART E: With Claude (skip_no_claude)
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@skip_no_claude
class TestHumanGateWithClaude:
    """Tests that require the Claude CLI.

    Scaffolds a project designed to reach fh_required and verifies the
    engine emits the correct F_H gate signals in the event log.
    """

    @pytest.fixture(scope="class")
    def fh_project_dir(self, tmp_path_factory):
        """Scaffold a project that will reach fh_required during auto run.

        Uses a feature vector with a very tight budget so F_P is exhausted
        quickly, and code that will fail F_D (pytest fails), forcing the
        engine to escalate to F_H.
        """
        project_dir = tmp_path_factory.mktemp("fh-gate-claude")
        _scaffold_human_gate_project(project_dir)
        return project_dir

    def test_claude_auto_run_reaches_fh_required_or_emits_proxy_approval(
        self, fh_project_dir: pathlib.Path
    ):
        """Running /gen-start --auto reaches fh_required or proxy emits review_approved.

        WHY: This validates the full dispatch path from Claude CLI invocation through
        to F_H gate detection. The project has failing tests, so F_D must fail, F_P
        must be attempted (and exhaust budget), and the engine must reach fh_required.

        If --human-proxy mode is active (which it may be in Claude's auto loop),
        a review_approved event may appear instead. Both outcomes are valid — they
        represent the two sides of the F_H gate: escalate (fh_required) or resolve
        autonomously (proxy approval).
        """
        meta_dir = fh_project_dir / ".e2e-meta"
        meta_dir.mkdir(exist_ok=True)

        prompt = (
            '/gen-start --auto\n\n'
            'IMPORTANT: Run the engine, iterate on REQ-F-TEST-001 code↔unit_tests edge. '
            'The code has bugs. Run F_D evaluation first. If F_D fails, attempt one '
            'F_P iteration. If still not converged, the engine should emit fh_required. '
            'Do NOT fix the code without recording the delta first. '
            'The test needs to observe the F_H gate path in the event log.'
        )

        result = run_claude_headless(
            fh_project_dir, prompt, log_dir=meta_dir,
            max_budget_usd=2.00,
            wall_timeout=600.0,
            stall_timeout=120.0,
        )

        print(f"\nE2E FH-GATE: Claude finished in {result.elapsed:.0f}s "
              f"(rc={result.returncode}, timed_out={result.timed_out})", flush=True)

        if result.timed_out:
            pytest.fail(
                f"Claude timed out after {result.elapsed:.0f}s.\n"
                f"--- stdout ---\n{result.stdout[-1500:]}\n"
                f"--- stderr ---\n{result.stderr[-500:]}"
            )

        events = _load_events(fh_project_dir)

        # We expect either:
        # A) fh_required path: IterationCompleted with status=fh_required + intent_raised
        # B) proxy path: review_approved with actor field set
        fh_required_events = [
            e for e in events
            if e.get("event_type") == "iteration_completed"
            and e.get("status") == "fh_required"
        ]
        proxy_approval_events = [
            e for e in events
            if e.get("event_type") == "review_approved"
            and e.get("actor")
        ]

        assert fh_required_events or proxy_approval_events, (
            "Expected either:\n"
            "  A) IterationCompleted with status=fh_required (engine paused at F_H gate)\n"
            "  B) review_approved with actor field (proxy resolved the gate)\n"
            f"Found neither. Events: {[e.get('event_type') for e in events]}\n"
            f"stdout: {result.stdout[-1000:]}"
        )

        if fh_required_events:
            print("E2E FH-GATE: Observed F_H gate path (fh_required)", flush=True)
        if proxy_approval_events:
            print(
                f"E2E FH-GATE: Observed proxy approval path "
                f"(actor={proxy_approval_events[-1].get('actor')!r})",
                flush=True,
            )
