# Validates: REQ-ITER-003, REQ-EVAL-002, REQ-SENSE-001, REQ-SUPV-003
"""UAT tests for the F_D functor framework — engine-level counterparts to test_functor_e2e.py.

These tests exercise the SAME 6 scenarios as test_functor_e2e.py, but through
the engine API (iterate_edge, run_edge, run) instead of hand-wiring individual
module calls. This enables comparison and analysis between:

  E2E  = manual pipeline: config_loader → fd_evaluate → fd_emit → fd_sense → ...
  UAT  = engine pipeline: engine.iterate_edge() / run_edge() / run()

Both should produce identical outcomes (delta, convergence, escalations, events).
Any divergence indicates a wiring bug in the engine.

Naming convention: TestUAT{N}_{name} mirrors TestE2E Scenario {N}.
"""

import json
import pathlib
import sys
import textwrap

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genesis.models import (
    Category,
    CheckOutcome,
    FunctionalUnit,
    CATEGORY_FIXED,
)
from genesis.config_loader import load_yaml, resolve_checklist
from genesis.engine import EngineConfig, IterationRecord, iterate_edge, run_edge, run
from genesis.fd_emit import make_event, emit_event
from genesis.fd_evaluate import evaluate_checklist, run_check
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


# ── Shared helpers (delegating to conftest) ─────────────────────────────

from conftest import (
    scaffold_green_project as _scaffold_green_project,
    green_constraints as _green_constraints,
    scaffold_broken_project as _scaffold_broken_project,
    red_constraints as _red_constraints,
    events_path as _events_path,
    read_events as _read_events,
)


def _make_engine_config(workspace_path, constraints, graph_topology=None):
    """Build an EngineConfig pointing at the real plugin configs."""
    return EngineConfig(
        project_name="uat_test",
        workspace_path=workspace_path,
        edge_params_dir=EDGE_PARAMS_DIR,
        profiles_dir=PROFILES_DIR,
        constraints=constraints,
        graph_topology=graph_topology or load_yaml(CONFIG_DIR / "graph_topology.yml"),
        model="sonnet",
        max_iterations_per_edge=3,
        claude_timeout=5,  # short — agent checks will timeout/error (by design)
    )


# ═══════════════════════════════════════════════════════════════════════════
# UAT SCENARIO 1: Green project via engine — matches E2E TestGreenProject
# ═══════════════════════════════════════════════════════════════════════════

class TestUAT1_GreenProject:
    """Green project through iterate_edge() — engine handles the full pipeline.

    E2E equivalent manually calls: resolve_checklist → evaluate_checklist →
    emit_event → sense_event_freshness → sense_req_tag_coverage → classify_signal_source

    UAT calls: iterate_edge() which does resolve + evaluate + emit internally,
    then verifies the same post-conditions with sense + classify.
    """

    @pytest.fixture
    def project(self, tmp_path):
        return _scaffold_green_project(tmp_path)

    @pytest.fixture
    def config(self, project):
        return _make_engine_config(project, _green_constraints())

    def test_engine_green_pipeline(self, project, config):
        """Engine iterate_edge() — all deterministic checks pass on green project.

        NOTE: The engine dispatches agent checks to fp_evaluate.run_check() which
        calls `claude -p` CLI. In the test environment (inside a Claude Code session),
        this returns ERROR — a real behavioral difference from E2E, which SKIPs agent
        checks via evaluate_checklist(). The engine's overall delta includes these
        agent ERRORs; we assert on deterministic-only delta for fair comparison.
        """
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
            iteration=1,
        )

        assert record.evaluation.edge == "code↔unit_tests"

        # Deterministic delta — zero on green project
        det_delta = sum(
            1 for cr in record.evaluation.checks
            if cr.required and cr.check_type == "deterministic"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        )
        assert det_delta == 0, f"Deterministic delta {det_delta} > 0 on green project"

        # All deterministic checks pass
        for cr in record.evaluation.checks:
            if cr.check_type == "deterministic" and not cr.message.startswith("Skipped"):
                assert cr.outcome == CheckOutcome.PASS, (
                    f"{cr.name} failed: {cr.message}\nstdout: {cr.stdout}\nstderr: {cr.stderr}"
                )
            if cr.check_type == "agent":
                # Engine dispatches to fp_evaluate — ERROR without claude CLI,
                # or SKIP if CLI not found on PATH
                assert cr.outcome in (CheckOutcome.SKIP, CheckOutcome.ERROR)

        # Agent ERRORs may inflate overall delta — document the difference
        agent_errors = sum(
            1 for cr in record.evaluation.checks
            if cr.required and cr.check_type == "agent"
            and cr.outcome == CheckOutcome.ERROR
        )
        if agent_errors > 0:
            # Expected in test env: engine delta > 0 due to agent ERRORs
            assert record.evaluation.delta == agent_errors
            assert record.evaluation.converged is False
        else:
            # If claude CLI happens to be available, full convergence
            assert record.evaluation.delta == 0
            assert record.evaluation.converged is True

    def test_engine_emits_events_automatically(self, project, config):
        """Engine always emits iteration_completed; edge_converged only if delta==0.

        In test env, agent checks ERROR → delta > 0 → no edge_converged event.
        We verify the iteration_completed event is always emitted with correct fields.
        """
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
        )

        events = _read_events(project)
        assert len(events) >= 1, f"Expected ≥1 event, got {len(events)}"

        types = [e["event_type"] for e in events]
        assert "iteration_completed" in types

        iter_event = next(e for e in events if e["event_type"] == "iteration_completed")
        assert iter_event["feature"] == "REQ-F-AUTH-001"
        assert iter_event["edge"] == "code↔unit_tests"

        if record.evaluation.converged:
            # Full convergence: both events emitted
            assert len(events) >= 2
            assert "edge_converged" in types
            assert iter_event["delta"] == 0
            assert iter_event["status"] == "converged"
        else:
            # Agent ERRORs prevented convergence — only iteration_completed
            assert iter_event["delta"] > 0
            assert iter_event["status"] == "iterating"
            assert "edge_converged" not in types

    def test_engine_events_pass_sense_checks(self, project, config):
        """Post-engine events pass freshness + integrity sensing."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
        )

        ep = _events_path(project)
        assert sense_event_freshness(ep, threshold_minutes=1).breached is False
        assert sense_event_log_integrity(ep).breached is False

    def test_engine_green_matches_e2e_delta(self, project, config):
        """Engine delta matches hand-wired E2E delta for the same project."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        constraints = config.constraints

        # E2E path (hand-wired)
        checks = resolve_checklist(edge_config, constraints)
        e2e_result = evaluate_checklist(checks, project, edge="code↔unit_tests")

        # UAT path (engine)
        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
        )

        # Compare: delta and convergence must match
        # Note: engine dispatches agent checks to fp_evaluate (which errors without
        # claude CLI), while E2E's evaluate_checklist skips them. But required
        # agent checks that ERROR would affect delta in engine path.
        # Since agent ERROR checks are required, they inflate engine delta.
        # Filter to deterministic-only for a fair comparison.
        e2e_det_delta = sum(
            1 for cr in e2e_result.checks
            if cr.required and cr.check_type == "deterministic"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        )
        engine_det_delta = sum(
            1 for cr in record.evaluation.checks
            if cr.required and cr.check_type == "deterministic"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        )

        assert e2e_det_delta == engine_det_delta, (
            f"Deterministic delta mismatch: E2E={e2e_det_delta}, Engine={engine_det_delta}"
        )

        # Both should have zero deterministic failures on a green project
        assert e2e_det_delta == 0
        assert engine_det_delta == 0


# ═══════════════════════════════════════════════════════════════════════════
# UAT SCENARIO 2: Red project via engine — matches E2E TestRedProject
# ═══════════════════════════════════════════════════════════════════════════

class TestUAT2_RedProject:
    """Broken project through engine — verifies η escalation and stall detection."""

    @pytest.fixture
    def project(self, tmp_path):
        return _scaffold_broken_project(tmp_path)

    @pytest.fixture
    def config(self, project):
        return _make_engine_config(project, _red_constraints())

    def test_engine_failing_tests_trigger_eta(self, project, config):
        """Engine iterate_edge() surfaces η_D→P escalation on test failure."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-CALC-001",
            asset_content="",
        )

        # Delta > 0 — same assertion as E2E
        assert record.evaluation.delta > 0, "Expected failing checks but delta is 0"
        assert record.evaluation.converged is False

        # η escalation should fire — engine uses "η_D→P:" prefix
        assert len(record.evaluation.escalations) > 0, "Expected η escalation"
        assert any("tests_pass" in e for e in record.evaluation.escalations), (
            f"Expected escalation for tests_pass, got: {record.evaluation.escalations}"
        )

    def test_engine_red_matches_e2e_deterministic_delta(self, project, config):
        """Engine deterministic delta matches hand-wired E2E on broken project."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        # E2E
        checks = resolve_checklist(edge_config, config.constraints)
        e2e_result = evaluate_checklist(checks, project, edge="code↔unit_tests")

        # Engine
        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-CALC-001",
            asset_content="",
        )

        # Compare deterministic deltas only (agent handling differs)
        e2e_det = sum(
            1 for cr in e2e_result.checks
            if cr.required and cr.check_type == "deterministic"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        )
        engine_det = sum(
            1 for cr in record.evaluation.checks
            if cr.required and cr.check_type == "deterministic"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        )

        assert e2e_det == engine_det, (
            f"Deterministic delta mismatch: E2E={e2e_det}, Engine={engine_det}"
        )
        assert e2e_det > 0  # at least tests_pass fails

    def test_engine_emits_non_converged_event(self, project, config):
        """Engine emits iteration_completed with status=iterating when delta > 0."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-CALC-001",
            asset_content="",
        )

        events = _read_events(project)
        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]
        assert len(iter_events) >= 1

        latest = iter_events[-1]
        assert latest["delta"] > 0
        assert latest["status"] == "iterating"
        assert latest.get("escalations", []) != []

        # NO edge_converged event
        converge_events = [e for e in events if e["event_type"] == "edge_converged"]
        assert len(converge_events) == 0

    def test_engine_run_edge_iterates_until_budget(self, project, config):
        """run_edge() iterates max_iterations_per_edge times on non-converging edge."""
        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-CALC-001",
            profile=load_yaml(PROFILES_DIR / "standard.yml"),
            asset_content="",
        )

        # Should iterate exactly max_iterations_per_edge times (bug never fixed)
        assert len(records) == config.max_iterations_per_edge
        assert all(not r.evaluation.converged for r in records)

        # Events emitted for each iteration
        events = _read_events(project)
        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]
        assert len(iter_events) == config.max_iterations_per_edge

    def test_engine_stall_detected_after_iterations(self, project, config):
        """After engine runs multiple iterations, sense detects stall."""
        run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-CALC-001",
            profile=load_yaml(PROFILES_DIR / "standard.yml"),
            asset_content="",
        )

        ep = _events_path(project)
        stall = sense_feature_stall(ep, "REQ-F-CALC-001", threshold_iterations=3)
        assert stall.breached is True, f"Expected stall after {config.max_iterations_per_edge} stuck iterations: {stall.detail}"


# ═══════════════════════════════════════════════════════════════════════════
# UAT SCENARIO 3: Profile-driven dispatch via engine — matches E2E TestProfileDrivenDispatch
# ═══════════════════════════════════════════════════════════════════════════

class TestUAT3_ProfileDispatch:
    """Profile encoding through the engine's routing — same assertions as E2E."""

    @pytest.fixture
    def profiles(self):
        result = {}
        for path in sorted(PROFILES_DIR.glob("*.yml")):
            result[path.stem] = load_yaml(path)
        return result

    def test_engine_uses_correct_profile_for_feature(self):
        """engine.run() selects standard profile for feature type."""
        assert select_profile("feature", PROFILES_DIR) == "standard"

    def test_engine_uses_correct_profile_for_hotfix(self):
        assert select_profile("hotfix", PROFILES_DIR) == "hotfix"

    def test_engine_uses_correct_profile_for_spike(self):
        assert select_profile("spike", PROFILES_DIR) == "spike"

    def test_all_profiles_emit_fd_invariant(self, profiles):
        """Emit is category-fixed F_D — same as E2E."""
        for name, profile in profiles.items():
            cat = lookup_encoding(profile, "emit")
            assert cat == Category.F_D, f"Profile {name}: emit should be F_D"

    def test_all_profiles_decide_fh_invariant(self, profiles):
        """Decide is category-fixed F_H — same as E2E."""
        for name, profile in profiles.items():
            cat = lookup_encoding(profile, "decide")
            assert cat == Category.F_H, f"Profile {name}: decide should be F_H"

    def test_engine_dispatch_standard_evaluate(self, profiles):
        """lookup_and_dispatch through engine's dispatch path."""
        fn = lookup_and_dispatch(FunctionalUnit.EVALUATE, profiles["standard"])
        assert fn is run_check

    def test_engine_dispatch_spike_evaluate_raises(self, profiles):
        """Spike F_P evaluate — not implemented."""
        with pytest.raises(NotImplementedError, match="F_P"):
            lookup_and_dispatch(FunctionalUnit.EVALUATE, profiles["spike"])

    def test_category_fixed_constant_matches_profiles(self):
        """CATEGORY_FIXED invariant — same as E2E."""
        assert CATEGORY_FIXED[FunctionalUnit.EMIT] == Category.F_D
        assert CATEGORY_FIXED[FunctionalUnit.DECIDE] == Category.F_H


# ═══════════════════════════════════════════════════════════════════════════
# UAT SCENARIO 4: Edge routing via engine.run() — matches E2E TestEdgeRouting
# ═══════════════════════════════════════════════════════════════════════════

class TestUAT4_EdgeRouting:
    """Full graph traversal routing through engine.run()."""

    @pytest.fixture
    def green_project(self, tmp_path):
        return _scaffold_green_project(tmp_path)

    @pytest.fixture
    def green_config(self, green_project):
        return _make_engine_config(green_project, _green_constraints())

    def test_engine_run_routes_through_edges(self, green_project, green_config):
        """engine.run() walks edges in profile order until one doesn't converge."""
        records = run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=green_config,
            asset_content="",
        )

        # Should have attempted at least the first edge
        assert len(records) >= 1

        # Check edges are from the standard profile's include list
        edges_attempted = list(dict.fromkeys(r.edge for r in records))
        standard = load_yaml(PROFILES_DIR / "standard.yml")
        profile_edges = standard["graph"]["include"]
        for edge in edges_attempted:
            assert edge in profile_edges, f"Engine attempted edge '{edge}' not in standard profile"

    def test_engine_run_starts_at_first_edge(self, green_project, green_config):
        """First record should be for intent→requirements."""
        records = run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=green_config,
            asset_content="",
        )
        assert records[0].edge == "intent→requirements"

    def test_engine_run_hotfix_skips_design(self, tmp_path):
        """Hotfix profile skips requirements→design — same as E2E."""
        project = _scaffold_green_project(tmp_path)
        config = _make_engine_config(project, _green_constraints())

        records = run(
            feature_id="HOTFIX-001",
            feature_type="hotfix",
            config=config,
            asset_content="",
        )

        edges_attempted = [r.edge for r in records]
        assert "requirements→design" not in edges_attempted

        hotfix = load_yaml(PROFILES_DIR / "hotfix.yml")
        hotfix_edges = hotfix["graph"]["include"]
        for edge in dict.fromkeys(edges_attempted):
            assert edge in hotfix_edges, f"Hotfix attempted '{edge}' not in hotfix profile"

    def test_engine_run_emits_events_for_each_edge(self, green_project, green_config):
        """Engine emits events for every iteration on every edge."""
        run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=green_config,
            asset_content="",
        )

        events = _read_events(green_project)
        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]
        assert len(iter_events) >= 1

        # All events should have project name
        for e in events:
            assert e["project"] == "uat_test"


# ═══════════════════════════════════════════════════════════════════════════
# UAT SCENARIO 5: Full lifecycle via engine — matches E2E TestFullLifecycle
# ═══════════════════════════════════════════════════════════════════════════

class TestUAT5_FullLifecycle:
    """Multi-iteration lifecycle through the engine, with sense + classify verification."""

    @pytest.fixture
    def project_with_history(self, tmp_path):
        """Project with pre-existing events (simulating prior iterations)."""
        project = _scaffold_green_project(tmp_path)

        # Pre-populate event history (2 prior iterations converging)
        ep = _events_path(project)
        ep.parent.mkdir(parents=True, exist_ok=True)
        for i, delta in enumerate([3, 1], 1):
            emit_event(ep, make_event(
                "iteration_completed",
                "uat_test",
                feature="REQ-F-AUTH-001",
                edge="code↔unit_tests",
                iteration=i,
                delta=delta,
            ))
        return project

    @pytest.fixture
    def config(self, project_with_history):
        return _make_engine_config(project_with_history, _green_constraints())

    def test_engine_appends_to_existing_events(self, project_with_history, config):
        """Engine events append to pre-existing event history.

        2 prior events + at least 1 new (iteration_completed). If converged,
        also edge_converged. Agent ERRORs may prevent convergence in test env.
        """
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
            iteration=3,
        )

        events = _read_events(project_with_history)
        # 2 prior + at least 1 new (iteration_completed)
        assert len(events) >= 3, f"Expected ≥3 events, got {len(events)}"

        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]
        assert iter_events[-1]["iteration"] == 3

        if record.evaluation.converged:
            # 2 prior + 2 new (iteration_completed + edge_converged)
            assert len(events) >= 4
            assert iter_events[-1]["delta"] == 0
        else:
            # Agent ERRORs: only iteration_completed, delta > 0
            assert iter_events[-1]["delta"] > 0

    def test_engine_event_trail_classifiable(self, project_with_history, config):
        """All events in the trail are classifiable by classify_signal_source."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
            iteration=3,
        )

        events = _read_events(project_with_history)
        signals = [classify_signal_source(e) for e in events]

        # All signals should be known categories, not "unknown"
        for i, sig in enumerate(signals):
            assert sig != "unknown", f"Event {i} ({events[i]['event_type']}) classified as unknown"

    def test_engine_no_stall_when_converging(self, project_with_history, config):
        """Converging delta sequence → no stall detected (matches E2E)."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
            iteration=3,
        )

        ep = _events_path(project_with_history)
        stall = sense_feature_stall(ep, "REQ-F-AUTH-001", threshold_iterations=3)
        assert stall.breached is False, f"False stall on converging sequence: {stall.detail}"

    def test_engine_req_coverage_after_iteration(self, project_with_history, config):
        """REQ tag coverage sense works on the scaffolded project."""
        coverage = sense_req_tag_coverage(
            project_with_history / "src", {"REQ-F-AUTH-001"}
        )
        assert coverage.breached is False
        assert coverage.value == 1.0

    def test_engine_event_integrity_after_lifecycle(self, project_with_history, config):
        """Full event log passes integrity check."""
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
            iteration=3,
        )

        ep = _events_path(project_with_history)
        integrity = sense_event_log_integrity(ep)
        assert integrity.breached is False, f"Log corrupt: {integrity.detail}"


# ═══════════════════════════════════════════════════════════════════════════
# UAT SCENARIO 6: Dispatch completeness via engine — matches E2E TestDispatchCompleteness
# ═══════════════════════════════════════════════════════════════════════════

class TestUAT6_DispatchCompleteness:
    """Verify dispatch table coverage — same checks as E2E, through engine imports."""

    def test_engine_all_fd_units_dispatched(self):
        """Every F_D unit in standard profile dispatches to a callable."""
        standard = load_yaml(PROFILES_DIR / "standard.yml")
        encoding = standard.get("encoding", {}).get("functional_units", {})

        for unit_name, cat_str in encoding.items():
            if cat_str != "F_D":
                continue
            unit = FunctionalUnit(unit_name)
            cat = Category(cat_str)
            fn = dispatch(unit, cat)
            assert callable(fn), f"({unit_name}, F_D) not callable"

    def test_engine_fp_fh_raise_not_implemented(self):
        """F_P and F_H stubs raise NotImplementedError."""
        standard = load_yaml(PROFILES_DIR / "standard.yml")
        encoding = standard.get("encoding", {}).get("functional_units", {})

        for unit_name, cat_str in encoding.items():
            if cat_str == "F_D":
                continue
            unit = FunctionalUnit(unit_name)
            cat = Category(cat_str)
            with pytest.raises(NotImplementedError):
                dispatch(unit, cat)

    def test_engine_dispatch_table_no_none(self):
        """No None values in the dispatch table."""
        for key, fn in DISPATCH.items():
            assert callable(fn), f"DISPATCH[{key}] not callable"


# ═══════════════════════════════════════════════════════════════════════════
# CROSS-METHOD COMPARISON: E2E vs UAT side-by-side
# ═══════════════════════════════════════════════════════════════════════════

class TestCrossMethodComparison:
    """Direct side-by-side comparison of E2E (hand-wired) vs UAT (engine)
    on the same project. Any divergence in deterministic results = bug.
    """

    @pytest.fixture
    def green_project(self, tmp_path):
        return _scaffold_green_project(tmp_path)

    @pytest.fixture
    def broken_project(self, tmp_path):
        return _scaffold_broken_project(tmp_path)

    def test_green_delta_identical(self, green_project):
        """Green project: E2E delta == engine delta for deterministic checks."""
        constraints = _green_constraints()
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        # E2E
        checks = resolve_checklist(edge_config, constraints)
        e2e = evaluate_checklist(checks, green_project, edge="code↔unit_tests")

        # Engine
        config = _make_engine_config(green_project, constraints)
        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="CMP-GREEN",
            asset_content="",
        )

        # Compare check-by-check for deterministic checks
        e2e_det = {cr.name: cr.outcome for cr in e2e.checks if cr.check_type == "deterministic"}
        eng_det = {cr.name: cr.outcome for cr in record.evaluation.checks if cr.check_type == "deterministic"}

        for name in e2e_det:
            assert name in eng_det, f"Check '{name}' in E2E but not engine"
            assert e2e_det[name] == eng_det[name], (
                f"Check '{name}' outcome differs: E2E={e2e_det[name]}, Engine={eng_det[name]}"
            )

    def test_red_delta_identical(self, broken_project):
        """Broken project: E2E delta == engine delta for deterministic checks."""
        constraints = _red_constraints()
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        # E2E
        checks = resolve_checklist(edge_config, constraints)
        e2e = evaluate_checklist(checks, broken_project, edge="code↔unit_tests")

        # Engine
        config = _make_engine_config(broken_project, constraints)
        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="CMP-RED",
            asset_content="",
        )

        # Compare deterministic outcomes check-by-check
        e2e_det = {cr.name: cr.outcome for cr in e2e.checks if cr.check_type == "deterministic"}
        eng_det = {cr.name: cr.outcome for cr in record.evaluation.checks if cr.check_type == "deterministic"}

        for name in e2e_det:
            assert name in eng_det, f"Check '{name}' in E2E but not engine"
            assert e2e_det[name] == eng_det[name], (
                f"Check '{name}' outcome differs: E2E={e2e_det[name]}, Engine={eng_det[name]}"
            )

    def test_green_check_names_identical(self, green_project):
        """Both methods produce the same set of check names."""
        constraints = _green_constraints()
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        checks = resolve_checklist(edge_config, constraints)
        e2e = evaluate_checklist(checks, green_project, edge="code↔unit_tests")

        config = _make_engine_config(green_project, constraints)
        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="CMP-NAMES",
            asset_content="",
        )

        e2e_names = sorted(cr.name for cr in e2e.checks)
        eng_names = sorted(cr.name for cr in record.evaluation.checks)
        assert e2e_names == eng_names

    def test_escalation_on_red_both_methods(self, broken_project):
        """Both methods produce η escalations for the same failing checks."""
        constraints = _red_constraints()
        edge_config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")

        checks = resolve_checklist(edge_config, constraints)
        e2e = evaluate_checklist(checks, broken_project, edge="code↔unit_tests")

        config = _make_engine_config(broken_project, constraints)
        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="CMP-ETA",
            asset_content="",
        )

        # Both should have escalations mentioning "tests_pass"
        assert any("tests_pass" in e for e in e2e.escalations), "E2E missing tests_pass escalation"
        assert any("tests_pass" in e for e in record.evaluation.escalations), "Engine missing tests_pass escalation"
