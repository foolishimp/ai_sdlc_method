# Validates: REQ-ITER-003, REQ-EVAL-002, REQ-SENSE-001, REQ-SUPV-003
"""E2E tests for the F_D functor framework.

These tests wire together the full pipeline:
  config_loader → resolve → evaluate → emit → sense → classify → route → dispatch

Each test simulates a realistic project scenario with real YAML configs,
real shell commands, and real event emission. The key behaviour under test
is the η (natural transformation) boundary: when deterministic checks fail,
the framework surfaces escalation signals that would hand off to F_P agents.
"""

import json
import pathlib
import sys
import textwrap

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genesis.models import (
    Category,
    CheckOutcome,
    FunctionalUnit,
    CATEGORY_FIXED,
)
from genesis.config_loader import load_yaml, resolve_checklist
from genesis.fd_evaluate import evaluate_checklist, run_check
from genesis.fd_emit import emit_event, make_event
from genesis.fd_classify import classify_req_tag, classify_source_finding, classify_signal_source
from genesis.fd_sense import (
    sense_event_freshness,
    sense_event_log_integrity,
    sense_feature_stall,
    sense_req_tag_coverage,
)
from genesis.fd_route import lookup_encoding, select_next_edge, select_profile
from genesis.dispatch import dispatch, lookup_and_dispatch, DISPATCH


# ── Paths to real configs ────────────────────────────────────────────────

PLUGIN_ROOT = (
    pathlib.Path(__file__).parent.parent
    / "code/.claude-plugin/plugins/genesis"
)
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 1: Green project — all deterministic checks pass, converges
# ═══════════════════════════════════════════════════════════════════════════

class TestGreenProject:
    """A well-structured project where all F_D checks pass.

    Pipeline: load tdd.yml → resolve with good constraints → run checks
    → all pass → delta=0 → converged → emit event → sense confirms health.
    """

    @pytest.fixture
    def project(self, tmp_path):
        """Scaffold a project that passes all deterministic checks."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "auth.py").write_text(textwrap.dedent("""\
            # Implements: REQ-F-AUTH-001
            def login(user: str, password: str) -> bool:
                return user == "admin" and password == "secret"
        """))

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_auth.py").write_text(textwrap.dedent("""\
            # Validates: REQ-F-AUTH-001
            from src.auth import login

            def test_login_success():
                assert login("admin", "secret") is True

            def test_login_failure():
                assert login("admin", "wrong") is False
        """))

        # pyproject.toml so pytest finds the package
        (tmp_path / "pyproject.toml").write_text(textwrap.dedent("""\
            [tool.pytest.ini_options]
            pythonpath = ["."]
        """))

        return tmp_path

    @pytest.fixture
    def constraints(self, project):
        """Project constraints with resolved tool paths."""
        return {
            "tools": {
                "test_runner": {
                    "command": "python -m pytest",
                    "args": "tests/ -v --tb=short",
                    "pass_criterion": "exit code 0",
                },
                "linter": {
                    "command": "python -m py_compile",
                    "args": "src/auth.py",
                    "pass_criterion": "exit code 0",
                },
                "formatter": {
                    "command": "true",  # stub — always passes
                    "args": "",
                    "pass_criterion": "exit code 0",
                },
                "coverage": {
                    "command": "python -m pytest",
                    "args": "tests/ --co -q",  # collect only — fast
                    "pass_criterion": "exit code 0",
                },
                "type_checker": {
                    "command": "true",
                    "args": "",
                    "pass_criterion": "exit code 0, zero errors",
                    "required": False,
                },
                "syntax_checker": {
                    "command": "python -m py_compile",
                    "args": "",
                    "pass_criterion": "exit code 0",
                },
            },
            "thresholds": {
                "test_coverage_minimum": 0.80,
                "max_function_lines": 50,
            },
            "standards": {
                "style_guide": "PEP 8",
                "docstrings": "recommended",
                "type_hints": "recommended",
                "test_structure": "AAA",
            },
        }

    def test_full_green_pipeline(self, project, constraints):
        """Load real TDD edge config, resolve, evaluate, emit, sense."""
        # 1. Load real edge config
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        assert "checklist" in edge_config

        # 2. Resolve $variables
        checks = resolve_checklist(edge_config, constraints)
        assert len(checks) > 0

        # Count check types
        det_checks = [c for c in checks if c.check_type == "deterministic"]
        agent_checks = [c for c in checks if c.check_type == "agent"]
        assert len(det_checks) >= 3, f"Expected ≥3 deterministic checks, got {len(det_checks)}"
        assert len(agent_checks) >= 3, f"Expected ≥3 agent checks, got {len(agent_checks)}"

        # 3. Evaluate — only deterministic checks run
        result = evaluate_checklist(checks, project, edge="code↔unit_tests")
        assert result.edge == "code↔unit_tests"

        # All deterministic checks should pass
        for cr in result.checks:
            if cr.check_type == "deterministic" and not cr.message.startswith("Skipped"):
                assert cr.outcome == CheckOutcome.PASS, (
                    f"{cr.name} failed: {cr.message}\nstdout: {cr.stdout}\nstderr: {cr.stderr}"
                )

        # Agent checks are SKIP (not F_D)
        for cr in result.checks:
            if cr.check_type == "agent":
                assert cr.outcome == CheckOutcome.SKIP

        # Delta should be 0 for deterministic checks (agent skips don't count)
        assert result.delta == 0, f"Delta {result.delta}: {[c.name for c in result.checks if c.outcome == CheckOutcome.FAIL]}"
        assert result.escalations == []

        # 4. Emit convergence event
        events_path = project / ".ai-workspace" / "events" / "events.jsonl"
        event = make_event(
            "iteration_completed",
            "test_project",
            feature="REQ-F-AUTH-001",
            edge="code↔unit_tests",
            delta=result.delta,
            status="converged" if result.converged else "iterating",
        )
        emit_event(events_path, event)

        # 5. Sense: verify event was written and is fresh
        freshness = sense_event_freshness(events_path, threshold_minutes=1)
        assert freshness.breached is False, f"Event stale: {freshness.detail}"

        integrity = sense_event_log_integrity(events_path)
        assert integrity.breached is False, f"Log corrupt: {integrity.detail}"

        # 6. Sense: REQ tag coverage
        coverage = sense_req_tag_coverage(project / "src", {"REQ-F-AUTH-001"})
        assert coverage.breached is False, f"Coverage gap: {coverage.detail}"

        # 7. Classify the event signal
        signal = classify_signal_source(json.loads(events_path.read_text().strip()))
        assert signal == "iteration"


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 2: Red project — deterministic checks fail, η fires
# ═══════════════════════════════════════════════════════════════════════════

class TestRedProject:
    """A project with failing tests — deterministic checks fail.

    This is the η boundary: F_D fails → escalation signal → F_P agent
    would investigate. We verify the escalation is surfaced correctly.
    """

    @pytest.fixture
    def broken_project(self, tmp_path):
        """Scaffold a project with a failing test."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "calc.py").write_text(textwrap.dedent("""\
            # Implements: REQ-F-CALC-001
            def add(a, b):
                return a - b  # BUG: subtraction instead of addition
        """))

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_calc.py").write_text(textwrap.dedent("""\
            # Validates: REQ-F-CALC-001
            from src.calc import add

            def test_add():
                assert add(2, 3) == 5  # will FAIL
        """))

        (tmp_path / "pyproject.toml").write_text(textwrap.dedent("""\
            [tool.pytest.ini_options]
            pythonpath = ["."]
        """))
        return tmp_path

    @pytest.fixture
    def constraints(self):
        return {
            "tools": {
                "test_runner": {
                    "command": "python -m pytest",
                    "args": "tests/ -v --tb=short",
                    "pass_criterion": "exit code 0",
                },
                "linter": {
                    "command": "python -m py_compile",
                    "args": "src/calc.py",
                    "pass_criterion": "exit code 0",
                },
                "formatter": {
                    "command": "true",
                    "args": "",
                    "pass_criterion": "exit code 0",
                },
                "coverage": {
                    "command": "true",
                    "args": "",
                    "pass_criterion": "exit code 0",
                },
                "type_checker": {
                    "command": "true",
                    "args": "",
                    "pass_criterion": "exit code 0",
                    "required": False,
                },
            },
            "thresholds": {"test_coverage_minimum": 0.80},
            "standards": {"style_guide": "PEP 8"},
        }

    def test_failing_tests_trigger_eta(self, broken_project, constraints):
        """When tests fail (F_D), the framework signals η_D→P escalation."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        checks = resolve_checklist(edge_config, constraints)

        result = evaluate_checklist(checks, broken_project, edge="code↔unit_tests")

        # Delta > 0 (tests_pass check fails)
        assert result.delta > 0, "Expected failing checks but delta is 0"
        assert result.converged is False

        # η escalation should fire for the failing check
        assert len(result.escalations) > 0, "Expected η_D→P escalation"
        assert any("tests_pass" in e for e in result.escalations), (
            f"Expected escalation for tests_pass, got: {result.escalations}"
        )

        # The specific test_pass check should be FAIL
        tests_pass = next((c for c in result.checks if c.name == "tests_pass"), None)
        assert tests_pass is not None
        assert tests_pass.outcome == CheckOutcome.FAIL
        assert tests_pass.exit_code != 0

    def test_emit_failing_iteration_then_sense_stall(self, broken_project, constraints):
        """Emit multiple failing iterations, then sense detects stall."""
        events_path = broken_project / "events.jsonl"

        # Simulate 4 iterations all stuck at delta=2
        for i in range(4):
            event = make_event(
                "iteration_completed",
                "test_project",
                feature="REQ-F-CALC-001",
                edge="code↔unit_tests",
                iteration=i + 1,
                delta=2,
                status="iterating",
            )
            emit_event(events_path, event)

        # Sense: stall detection
        stall = sense_feature_stall(events_path, "REQ-F-CALC-001", threshold_iterations=3)
        assert stall.breached is True, f"Expected stall detection: {stall.detail}"

        # Classify the stall as an escalation signal
        finding = classify_source_finding(
            f"Feature REQ-F-CALC-001 delta unchanged for 4 iterations — unclear root cause"
        )
        assert finding.classification == "SOURCE_AMBIGUITY"

    def test_mixed_pass_fail_delta_counts_only_required(self, broken_project, constraints):
        """Non-required checks that fail don't inflate delta."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        checks = resolve_checklist(edge_config, constraints)

        # Count required deterministic checks
        req_det = [c for c in checks if c.check_type == "deterministic" and c.required and not c.unresolved]
        # type_checker.required is False, so it should be excluded
        type_check = next((c for c in checks if c.name == "type_check"), None)
        if type_check:
            assert type_check.required is False

        result = evaluate_checklist(checks, broken_project, edge="code↔unit_tests")

        # Only required failing deterministic checks count toward delta
        failing_required = [
            c for c in result.checks
            if c.required and c.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        ]
        assert result.delta == len(failing_required)


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 3: Profile-driven dispatch — different profiles route differently
# ═══════════════════════════════════════════════════════════════════════════

class TestProfileDrivenDispatch:
    """Different profiles encode functional units to different categories.

    Standard: evaluate→F_D, route→F_H
    Hotfix:   evaluate→F_D, route→F_D (emergency, no human routing)
    Spike:    evaluate→F_P, route→F_P (exploration, agent picks)

    The dispatch table must route to the correct callable or raise
    NotImplementedError for unimplemented categories.
    """

    @pytest.fixture
    def profiles(self):
        """Load all real profile YAMLs."""
        result = {}
        for path in sorted(PROFILES_DIR.glob("*.yml")):
            result[path.stem] = load_yaml(path)
        return result

    def test_standard_evaluate_is_fd(self, profiles):
        """Standard profile: evaluate is deterministic."""
        cat = lookup_encoding(profiles["standard"], "evaluate")
        assert cat == Category.F_D
        fn = dispatch(FunctionalUnit.EVALUATE, cat)
        assert fn is run_check

    def test_standard_route_is_fh(self, profiles):
        """Standard profile: route is human — not implemented yet."""
        cat = lookup_encoding(profiles["standard"], "route")
        assert cat == Category.F_H
        with pytest.raises(NotImplementedError):
            dispatch(FunctionalUnit.ROUTE, cat)

    def test_hotfix_route_is_fd(self, profiles):
        """Hotfix profile: route is deterministic (emergency fixed path)."""
        cat = lookup_encoding(profiles["hotfix"], "route")
        assert cat == Category.F_D
        fn = dispatch(FunctionalUnit.ROUTE, cat)
        assert callable(fn)

    def test_spike_evaluate_is_fp(self, profiles):
        """Spike profile: evaluate is probabilistic (agent explores)."""
        cat = lookup_encoding(profiles["spike"], "evaluate")
        assert cat == Category.F_P
        with pytest.raises(NotImplementedError):
            dispatch(FunctionalUnit.EVALUATE, cat)

    def test_all_profiles_have_emit_fd(self, profiles):
        """Emit is category-fixed F_D across ALL profiles."""
        for name, profile in profiles.items():
            cat = lookup_encoding(profile, "emit")
            assert cat == Category.F_D, f"Profile {name}: emit should be F_D, got {cat}"

    def test_all_profiles_have_decide_fh(self, profiles):
        """Decide is category-fixed F_H across ALL profiles."""
        for name, profile in profiles.items():
            cat = lookup_encoding(profile, "decide")
            assert cat == Category.F_H, f"Profile {name}: decide should be F_H, got {cat}"

    def test_category_fixed_invariant(self):
        """CATEGORY_FIXED model constant matches profile data."""
        assert CATEGORY_FIXED[FunctionalUnit.EMIT] == Category.F_D
        assert CATEGORY_FIXED[FunctionalUnit.DECIDE] == Category.F_H

    def test_lookup_and_dispatch_standard_evaluate(self, profiles):
        """End-to-end: profile → encoding → category → callable."""
        fn = lookup_and_dispatch(FunctionalUnit.EVALUATE, profiles["standard"])
        assert fn is run_check

    def test_lookup_and_dispatch_spike_evaluate_raises(self, profiles):
        """Spike evaluate is F_P — dispatch raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="F_P"):
            lookup_and_dispatch(FunctionalUnit.EVALUATE, profiles["spike"])


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 4: Edge routing — feature traversal through the graph
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeRouting:
    """Route a feature through edges, verifying selection logic."""

    @pytest.fixture
    def standard_profile(self):
        return load_yaml(PROFILES_DIR / "standard.yml")

    @pytest.fixture
    def hotfix_profile(self):
        return load_yaml(PROFILES_DIR / "hotfix.yml")

    def test_new_feature_starts_at_intent(self, standard_profile):
        """Empty trajectory → first edge in profile."""
        route = select_next_edge({"trajectory": {}}, {}, standard_profile)
        assert route.selected_edge == "intent→requirements"
        assert route.profile == "standard"

    def test_mid_feature_routes_to_next(self, standard_profile):
        """Some edges converged → routes to first unconverged."""
        trajectory = {
            "trajectory": {
                "intent_requirements": {"status": "converged"},
                "requirements_design": {"status": "converged"},
                "design_code": {"status": "iterating"},
            }
        }
        route = select_next_edge(trajectory, {}, standard_profile)
        assert route.selected_edge == "design→code"

    def test_all_converged_returns_empty(self, standard_profile):
        """All edges converged → no next edge."""
        trajectory = {
            "trajectory": {
                "intent_requirements": {"status": "converged"},
                "requirements_design": {"status": "converged"},
                "design_code": {"status": "converged"},
                "code_unit_tests": {"status": "converged"},
            }
        }
        route = select_next_edge(trajectory, {}, standard_profile)
        assert route.selected_edge == ""

    def test_hotfix_skips_design(self, hotfix_profile):
        """Hotfix profile skips requirements→design, goes intent→requirements→design→code."""
        trajectory = {
            "trajectory": {
                "intent_requirements": {"status": "converged"},
            }
        }
        route = select_next_edge(trajectory, {}, hotfix_profile)
        # Hotfix includes: intent→requirements, design→code, code↔unit_tests
        assert route.selected_edge == "design→code"

    def test_profile_selection_from_vector_type(self):
        """Vector type maps to correct profile."""
        assert select_profile("feature", PROFILES_DIR) == "standard"
        assert select_profile("hotfix", PROFILES_DIR) == "hotfix"
        assert select_profile("spike", PROFILES_DIR) == "spike"
        assert select_profile("discovery", PROFILES_DIR) == "poc"


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 5: Full lifecycle — resolve → evaluate → emit → sense → classify
# ═══════════════════════════════════════════════════════════════════════════

class TestFullLifecycle:
    """Wire the entire F_D pipeline across multiple iterations,
    demonstrating the η boundary where F_D hands off to F_P.
    """

    @pytest.fixture
    def project_with_events(self, tmp_path):
        """Project with pre-existing event history."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "api.py").write_text(textwrap.dedent("""\
            # Implements: REQ-F-API-001
            def get_users():
                return [{"id": 1, "name": "Alice"}]
        """))

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        # Write 2 prior iterations (converging)
        for i, delta in enumerate([3, 1], 1):
            event = make_event(
                "iteration_completed",
                "lifecycle_test",
                feature="REQ-F-API-001",
                edge="code↔unit_tests",
                iteration=i,
                delta=delta,
            )
            emit_event(events_path, event)

        return tmp_path, events_path

    def test_converging_feature_no_stall(self, project_with_events):
        """Decreasing deltas → no stall detected."""
        _, events_path = project_with_events
        stall = sense_feature_stall(events_path, "REQ-F-API-001", threshold_iterations=3)
        assert stall.breached is False

    def test_emit_convergence_and_verify(self, project_with_events):
        """Emit a converged iteration, then verify the full event trail."""
        project, events_path = project_with_events

        # Iteration 3: converged
        event = make_event(
            "iteration_completed",
            "lifecycle_test",
            feature="REQ-F-API-001",
            edge="code↔unit_tests",
            iteration=3,
            delta=0,
            status="converged",
        )
        emit_event(events_path, event)

        # Emit edge_converged event
        converge_event = make_event(
            "edge_converged",
            "lifecycle_test",
            feature="REQ-F-API-001",
            edge="code↔unit_tests",
        )
        emit_event(events_path, converge_event)

        # Verify log integrity
        integrity = sense_event_log_integrity(events_path)
        assert integrity.breached is False
        assert integrity.value == 4  # 2 prior + 2 new

        # Classify signals
        lines = events_path.read_text().strip().split("\n")
        signals = [classify_signal_source(json.loads(l)) for l in lines]
        assert signals == ["iteration", "iteration", "iteration", "convergence"]

    def test_req_coverage_across_sense_and_classify(self, project_with_events):
        """Sense REQ coverage, then classify each tag found."""
        project, _ = project_with_events

        # Sense
        coverage = sense_req_tag_coverage(project / "src", {"REQ-F-API-001", "REQ-F-API-002"})
        assert coverage.value == 0.5  # only API-001 present
        assert coverage.breached is True

        # Classify the tags we do find
        tag_result = classify_req_tag("Implements: REQ-F-API-001")
        assert tag_result.classification == "VALID"

        # Classify the gap
        gap = classify_source_finding("REQ-F-API-002 is missing from all source files")
        assert gap.classification == "SOURCE_GAP"


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 6: Dispatch table completeness
# ═══════════════════════════════════════════════════════════════════════════

class TestDispatchCompleteness:
    """Verify the dispatch table covers all F_D units from the standard profile."""

    def test_all_fd_units_in_standard_profile_are_dispatched(self):
        """Every unit encoded as F_D in standard profile has a dispatch entry."""
        standard = load_yaml(PROFILES_DIR / "standard.yml")
        encoding = standard.get("encoding", {}).get("functional_units", {})

        for unit_name, cat_str in encoding.items():
            if cat_str != "F_D":
                continue
            unit = FunctionalUnit(unit_name)
            cat = Category(cat_str)
            fn = dispatch(unit, cat)
            assert callable(fn), f"({unit_name}, F_D) dispatch returned non-callable: {fn}"

    def test_fp_fh_units_raise_not_implemented(self):
        """F_P and F_H units are stubs — they raise NotImplementedError."""
        standard = load_yaml(PROFILES_DIR / "standard.yml")
        encoding = standard.get("encoding", {}).get("functional_units", {})

        for unit_name, cat_str in encoding.items():
            if cat_str == "F_D":
                continue
            unit = FunctionalUnit(unit_name)
            cat = Category(cat_str)
            with pytest.raises(NotImplementedError):
                dispatch(unit, cat)

    def test_dispatch_table_has_no_none_values(self):
        """Every entry in the dispatch table is a real callable."""
        for key, fn in DISPATCH.items():
            assert callable(fn), f"DISPATCH[{key}] is not callable: {fn}"
