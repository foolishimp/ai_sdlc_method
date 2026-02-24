# Validates: REQ-ITER-003, REQ-EVAL-002, REQ-SENSE-001, REQ-SUPV-003
"""Complex test scenarios — cost-benefit boundary analysis.

These tests stress the boundary between the E2E agent model (1 headless Claude
session) and the deterministic engine model (many `claude -p` cold-start calls).
They exercise gaps identified in FRAMEWORK_COMPARISON_ANALYSIS.md:

  A. Agent-dominated edges (intent→requirements — worst-case engine cost)
  B. Multi-edge traversal through engine.run()
  C. Profile-parameterized engine runs (hotfix, spike, minimal)
  D. η escalation chain across iterations
  E. Multi-feature workspace
  F. Cost model validation (check counts per edge/profile)

All tests are deterministic (no LLM calls) — agent checks ERROR/SKIP by design.
"""

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genisis.models import CheckOutcome
from genisis.config_loader import load_yaml, resolve_checklist
from genisis.engine import EngineConfig, iterate_edge, run_edge, run
from genisis.fd_emit import make_event, emit_event
from genisis.fd_sense import sense_feature_stall, sense_event_log_integrity

from conftest import (
    scaffold_green_project,
    green_constraints,
    scaffold_broken_project,
    red_constraints,
    make_engine_config,
    events_path,
    read_events,
    EDGE_PARAMS_DIR,
    PROFILES_DIR,
    CONFIG_DIR,
)


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

STANDARD_EDGES = [
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
]

HOTFIX_EDGES = [
    "intent→requirements",
    "design→code",
    "code↔unit_tests",
]

EDGE_TO_FILE = {
    "intent→requirements": "intent_requirements",
    "requirements→design": "requirements_design",
    "design→code": "design_code",
    "code↔unit_tests": "tdd",
}


def _load_edge_config(edge_name):
    """Load edge config by edge name."""
    filename = EDGE_TO_FILE.get(edge_name, edge_name.replace("→", "_").replace("↔", "_"))
    return load_yaml(EDGE_PARAMS_DIR / f"{filename}.yml")


def _count_check_types(checks):
    """Count checks by type. Returns dict: {type: count}."""
    counts = {"deterministic": 0, "agent": 0, "human": 0}
    for c in checks:
        t = c.check_type
        if t in counts:
            counts[t] += 1
    return counts


def _count_required_check_types(checks):
    """Count required checks by type."""
    counts = {"deterministic": 0, "agent": 0, "human": 0}
    for c in checks:
        if c.required and c.check_type in counts:
            counts[c.check_type] += 1
    return counts


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO F: Cost Model Validation
# ═══════════════════════════════════════════════════════════════════════════

class TestCostModel:
    """Validate check-count cost model from FRAMEWORK_COMPARISON_ANALYSIS.md.

    Pure data tests — load configs, resolve checklists, count check types.
    No engine calls, no subprocess execution.
    """

    @pytest.fixture
    def constraints(self):
        return green_constraints()

    def test_standard_profile_total_check_count(self, constraints):
        """Load all 4 standard-profile edge configs, resolve, count total checks."""
        total = 0
        by_type = {"deterministic": 0, "agent": 0, "human": 0}
        for edge in STANDARD_EDGES:
            ec = _load_edge_config(edge)
            checks = resolve_checklist(ec, constraints)
            total += len(checks)
            counts = _count_check_types(checks)
            for t in by_type:
                by_type[t] += counts[t]

        # Sanity: standard profile has a meaningful number of checks
        assert total >= 40, f"Expected ≥40 total checks across standard edges, got {total}"
        assert by_type["deterministic"] >= 8, f"Expected ≥8 deterministic, got {by_type}"
        assert by_type["agent"] >= 25, f"Expected ≥25 agent, got {by_type}"
        assert by_type["human"] >= 3, f"Expected ≥3 human, got {by_type}"

    def test_hotfix_profile_total_check_count(self, constraints):
        """Hotfix profile has fewer total checks than standard."""
        standard_total = sum(
            len(resolve_checklist(_load_edge_config(e), constraints))
            for e in STANDARD_EDGES
        )
        hotfix_total = sum(
            len(resolve_checklist(_load_edge_config(e), constraints))
            for e in HOTFIX_EDGES
        )
        assert hotfix_total < standard_total, (
            f"Hotfix ({hotfix_total}) should have fewer checks than standard ({standard_total})"
        )

    def test_deterministic_to_agent_ratio_per_edge(self, constraints):
        """code↔unit_tests has highest det:agent ratio; intent→requirements has lowest."""
        ratios = {}
        for edge in STANDARD_EDGES:
            ec = _load_edge_config(edge)
            checks = resolve_checklist(ec, constraints)
            counts = _count_check_types(checks)
            agent = counts["agent"] or 0.001  # avoid div-by-zero
            ratios[edge] = counts["deterministic"] / agent

        assert ratios["code↔unit_tests"] > ratios["intent→requirements"], (
            f"TDD det:agent ({ratios['code↔unit_tests']:.2f}) should be > "
            f"intent→req det:agent ({ratios['intent→requirements']:.2f})"
        )
        # intent→requirements should have 0 deterministic checks
        assert ratios["intent→requirements"] < 0.01, (
            f"intent→requirements should have ~0 deterministic, ratio={ratios['intent→requirements']:.3f}"
        )

    def test_cost_model_agent_check_counts_per_edge(self, constraints):
        """Document agent check counts per edge — this is the engine's claude -p call count."""
        expected_minimums = {
            "intent→requirements": 10,  # heavily agent-dominated
            "requirements→design": 10,
            "design→code": 2,
            "code↔unit_tests": 5,
        }
        for edge, min_agent in expected_minimums.items():
            ec = _load_edge_config(edge)
            checks = resolve_checklist(ec, constraints)
            agent_count = sum(1 for c in checks if c.check_type == "agent")
            assert agent_count >= min_agent, (
                f"{edge}: expected ≥{min_agent} agent checks, got {agent_count}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO A: Agent-Dominated Edge (intent→requirements)
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentDominatedEdge:
    """Stress-test the engine on intent→requirements — worst-case cost scenario.

    This edge has ~12 agent checks, 2 human checks, 0 deterministic checks.
    The engine makes 1 cold-start `claude -p` per agent check.
    """

    @pytest.fixture
    def constraints(self):
        return green_constraints()

    @pytest.fixture
    def edge_config(self):
        return _load_edge_config("intent→requirements")

    def test_intent_requirements_check_distribution(self, edge_config, constraints):
        """Verify intent→requirements is agent-dominated."""
        checks = resolve_checklist(edge_config, constraints)
        counts = _count_check_types(checks)

        assert counts["agent"] >= 10, f"Expected ≥10 agent checks, got {counts['agent']}"
        assert counts["human"] >= 2, f"Expected ≥2 human checks, got {counts['human']}"
        assert counts["deterministic"] == 0, (
            f"Expected 0 deterministic checks, got {counts['deterministic']}"
        )

    def test_intent_requirements_engine_all_agent_errors(self, tmp_path, edge_config, constraints):
        """Run iterate_edge() on intent→requirements — all agent checks ERROR/SKIP."""
        project = scaffold_green_project(tmp_path)
        config = make_engine_config(project, constraints)

        record = iterate_edge(
            edge="intent→requirements",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
            iteration=1,
        )

        # All agent checks should ERROR or SKIP (no claude CLI in test)
        for cr in record.evaluation.checks:
            if cr.check_type == "agent":
                assert cr.outcome in (CheckOutcome.ERROR, CheckOutcome.SKIP), (
                    f"Agent check {cr.name} unexpectedly {cr.outcome}"
                )
            if cr.check_type == "human":
                assert cr.outcome == CheckOutcome.SKIP

        # Delta = count of required checks that ERROR (all agent)
        required_agent = sum(
            1 for cr in record.evaluation.checks
            if cr.required and cr.check_type == "agent"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
        )
        # No deterministic checks to provide "free" signal
        det_pass = sum(
            1 for cr in record.evaluation.checks
            if cr.check_type == "deterministic" and cr.outcome == CheckOutcome.PASS
        )
        assert det_pass == 0, "intent→requirements should have 0 deterministic passes"
        assert required_agent > 0, "Expected required agent ERRORs"

    def test_intent_requirements_vs_tdd_cost_ratio(self, constraints):
        """Compare agent:deterministic ratio across edges.

        intent→requirements has highest ratio (all agent, no deterministic).
        code↔unit_tests has lowest ratio (many deterministic).
        """
        ir_checks = resolve_checklist(_load_edge_config("intent→requirements"), constraints)
        tdd_checks = resolve_checklist(_load_edge_config("code↔unit_tests"), constraints)

        ir_counts = _count_check_types(ir_checks)
        tdd_counts = _count_check_types(tdd_checks)

        # intent→requirements: all agent, no deterministic
        assert ir_counts["deterministic"] == 0
        assert ir_counts["agent"] > 0

        # code↔unit_tests: some deterministic, some agent
        assert tdd_counts["deterministic"] > 0
        assert tdd_counts["agent"] > 0

        # TDD has the best ratio (more "free" deterministic checks)
        tdd_ratio = tdd_counts["deterministic"] / (tdd_counts["agent"] or 1)
        assert tdd_ratio > 0.5, f"TDD det:agent ratio ({tdd_ratio:.2f}) should be > 0.5"


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO B: Multi-Edge Traversal Through Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestMultiEdgeTraversal:
    """Verify run() traverses multiple edges and trajectory propagates correctly."""

    @pytest.fixture
    def project(self, tmp_path):
        return scaffold_green_project(tmp_path)

    @pytest.fixture
    def config(self, project):
        return make_engine_config(project, green_constraints())

    def test_engine_run_traverses_multiple_edges(self, project, config):
        """run() should attempt at least the first edge and stop at non-convergence."""
        records = run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=config,
            asset_content="",
        )

        assert len(records) >= 1, "Expected at least 1 iteration record"
        # First edge attempted should be intent→requirements
        assert records[0].edge == "intent→requirements"

        # Collect distinct edges attempted
        edges_attempted = list(dict.fromkeys(r.edge for r in records))
        assert len(edges_attempted) >= 1

    def test_engine_run_stops_on_first_non_converging_edge(self, project, config):
        """Engine stops at the first non-converging edge (agent ERRORs block)."""
        records = run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=config,
            asset_content="",
        )

        # intent→requirements has only agent checks, which ERROR in test env
        # So the engine should stop at intent→requirements
        edges = list(dict.fromkeys(r.edge for r in records))

        # The last edge should NOT have converged (agent ERRORs)
        last_records_for_edge = [r for r in records if r.edge == edges[-1]]
        assert not last_records_for_edge[-1].evaluation.converged, (
            f"Expected non-convergence on {edges[-1]} due to agent ERRORs"
        )

    def test_engine_run_emits_events_for_all_attempted_edges(self, project, config):
        """Events are emitted for every iteration on every attempted edge."""
        records = run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=config,
            asset_content="",
        )

        events = read_events(project)
        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]
        assert len(iter_events) >= 1

        # Each record should have a corresponding event
        assert len(iter_events) >= len(records), (
            f"Expected ≥{len(records)} iteration events, got {len(iter_events)}"
        )

        # All events have correct project name
        for e in events:
            assert e["project"] == "test_project"

    def test_engine_run_trajectory_accumulates(self, project, config):
        """After run(), trajectory reflects edge status across all attempted edges.

        We verify indirectly: the records list shows which edges were attempted
        and their convergence status.
        """
        records = run(
            feature_id="REQ-F-AUTH-001",
            feature_type="feature",
            config=config,
            asset_content="",
        )

        # Group records by edge
        by_edge = {}
        for r in records:
            by_edge.setdefault(r.edge, []).append(r)

        # Each edge should have iteration numbers starting at 1
        for edge, edge_records in by_edge.items():
            iterations = [r.iteration for r in edge_records]
            assert iterations[0] == 1, f"Edge {edge} should start at iteration 1"
            # Iterations should be sequential
            for i, it in enumerate(iterations):
                assert it == i + 1, f"Edge {edge}: expected iteration {i+1}, got {it}"


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO C: Profile-Parameterized Engine Runs
# ═══════════════════════════════════════════════════════════════════════════

class TestProfileParameterized:
    """Run the engine with different profiles — verify graph subset and behavior differ."""

    @pytest.fixture
    def project(self, tmp_path):
        return scaffold_green_project(tmp_path)

    def _run_with_type(self, project, feature_type):
        config = make_engine_config(project, green_constraints())
        return run(
            feature_id=f"TEST-{feature_type.upper()}-001",
            feature_type=feature_type,
            config=config,
            asset_content="",
        )

    def test_hotfix_profile_skips_requirements_design(self, project):
        """Hotfix skips requirements→design edge."""
        records = self._run_with_type(project, "hotfix")
        edges_attempted = list(dict.fromkeys(r.edge for r in records))
        assert "requirements→design" not in edges_attempted

        hotfix_profile = load_yaml(PROFILES_DIR / "hotfix.yml")
        hotfix_edges = hotfix_profile["graph"]["include"]
        for edge in edges_attempted:
            assert edge in hotfix_edges, f"Edge '{edge}' not in hotfix profile"

    def test_hotfix_vs_standard_check_count_ratio(self):
        """Hotfix has fewer total checks than standard."""
        constraints = green_constraints()

        standard_total = sum(
            len(resolve_checklist(_load_edge_config(e), constraints))
            for e in STANDARD_EDGES
        )
        hotfix_total = sum(
            len(resolve_checklist(_load_edge_config(e), constraints))
            for e in HOTFIX_EDGES
        )

        # Hotfix: 3 edges, standard: 4 edges — hotfix should be smaller
        assert hotfix_total < standard_total

    def test_hotfix_tdd_edge_deterministic_dominant(self):
        """For hotfix code↔unit_tests, deterministic checks outnumber human checks."""
        constraints = green_constraints()
        checks = resolve_checklist(_load_edge_config("code↔unit_tests"), constraints)
        counts = _count_check_types(checks)

        # TDD edge has many deterministic checks — should be dominant over human
        assert counts["deterministic"] > counts["human"], (
            f"TDD: det={counts['deterministic']}, human={counts['human']}"
        )

    def test_spike_profile_edges(self, project):
        """Spike profile includes only intent→requirements, requirements→design, design→code."""
        records = self._run_with_type(project, "spike")
        edges_attempted = list(dict.fromkeys(r.edge for r in records))

        spike_profile = load_yaml(PROFILES_DIR / "spike.yml")
        spike_edges = spike_profile["graph"]["include"]

        for edge in edges_attempted:
            assert edge in spike_edges, f"Edge '{edge}' not in spike profile"

        # code↔unit_tests should NOT be attempted
        assert "code↔unit_tests" not in edges_attempted

    def test_minimal_profile_fewest_edges(self, project):
        """Minimal profile has only 2 edges — fewer than any other profile."""
        minimal_profile = load_yaml(PROFILES_DIR / "minimal.yml")
        minimal_edges = minimal_profile["graph"]["include"]
        assert len(minimal_edges) == 2, f"Minimal should have 2 edges, got {len(minimal_edges)}"

        # Compare with other profiles
        for profile_name in ["standard", "hotfix", "spike", "poc"]:
            p = load_yaml(PROFILES_DIR / f"{profile_name}.yml")
            other_edges = p["graph"]["include"]
            assert len(minimal_edges) <= len(other_edges), (
                f"Minimal ({len(minimal_edges)}) should be ≤ {profile_name} ({len(other_edges)})"
            )


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO D: η Escalation Chain
# ═══════════════════════════════════════════════════════════════════════════

class TestEtaEscalationChain:
    """Verify η escalation propagation — F_D fails → η_D→P, agent fails → η_P→H."""

    @pytest.fixture
    def broken_project(self, tmp_path):
        return scaffold_broken_project(tmp_path)

    @pytest.fixture
    def broken_config(self, broken_project):
        return make_engine_config(broken_project, red_constraints())

    def test_eta_dp_on_deterministic_failure(self, broken_project, broken_config):
        """iterate_edge() on broken project produces η_D→P escalations."""
        edge_config = _load_edge_config("code↔unit_tests")

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=broken_config,
            feature_id="REQ-F-CALC-001",
            asset_content="",
        )

        # Deterministic failures produce η_D→P escalations
        dp_escalations = [e for e in record.evaluation.escalations if "η_D→P:" in e]
        assert len(dp_escalations) > 0, (
            f"Expected η_D→P escalations, got: {record.evaluation.escalations}"
        )
        assert any("tests_pass" in e for e in dp_escalations), (
            f"Expected tests_pass in η_D→P escalations: {dp_escalations}"
        )

    def test_eta_ph_on_agent_error(self, tmp_path):
        """iterate_edge() where agent checks ERROR produces η_P→H escalations."""
        project = scaffold_green_project(tmp_path)
        config = make_engine_config(project, green_constraints())
        edge_config = _load_edge_config("intent→requirements")

        record = iterate_edge(
            edge="intent→requirements",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="",
        )

        # Agent ERRORs produce η_P→H escalations
        ph_escalations = [e for e in record.evaluation.escalations if "η_P→H:" in e]
        assert len(ph_escalations) > 0, (
            f"Expected η_P→H escalations from agent ERRORs, got: {record.evaluation.escalations}"
        )

    def test_eta_chain_across_iterations(self, broken_project, broken_config):
        """run_edge() with max_iterations — each iteration has escalations."""
        records = run_edge(
            edge="code↔unit_tests",
            config=broken_config,
            feature_id="REQ-F-CALC-001",
            profile=load_yaml(PROFILES_DIR / "standard.yml"),
            asset_content="",
        )

        # Should iterate max_iterations_per_edge times (bug never fixed)
        assert len(records) == broken_config.max_iterations_per_edge

        # Each iteration should have escalations
        for i, record in enumerate(records):
            assert len(record.evaluation.escalations) > 0, (
                f"Iteration {i+1}: expected escalations, got none"
            )

        # Events should contain escalation data
        events = read_events(broken_project)
        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]
        for ev in iter_events:
            assert len(ev.get("escalations", [])) > 0, (
                f"Event for iteration {ev.get('iteration')} missing escalations"
            )

    def test_eta_count_matches_delta(self, broken_project, broken_config):
        """Number of escalations equals delta for each iteration."""
        edge_config = _load_edge_config("code↔unit_tests")

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=broken_config,
            feature_id="REQ-F-CALC-001",
            asset_content="",
        )

        # Each escalation corresponds to one failing required check
        assert len(record.evaluation.escalations) == record.evaluation.delta, (
            f"Escalations ({len(record.evaluation.escalations)}) should equal "
            f"delta ({record.evaluation.delta})"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO E: Multi-Feature Workspace
# ═══════════════════════════════════════════════════════════════════════════

class TestMultiFeatureWorkspace:
    """Verify two features can share the same workspace without interference."""

    def test_two_features_same_workspace(self, tmp_path):
        """Run iterate_edge() for two features — events correctly attributed."""
        project = scaffold_green_project(tmp_path)
        config = make_engine_config(project, green_constraints())
        edge_config = _load_edge_config("code↔unit_tests")

        for feature_id in ["FEAT-001", "FEAT-002"]:
            iterate_edge(
                edge="code↔unit_tests",
                edge_config=edge_config,
                config=config,
                feature_id=feature_id,
                asset_content="",
            )

        events = read_events(project)
        iter_events = [e for e in events if e["event_type"] == "iteration_completed"]

        # Both features should have events
        features_in_events = {e["feature"] for e in iter_events}
        assert "FEAT-001" in features_in_events
        assert "FEAT-002" in features_in_events

        # No cross-contamination — each event attributed to correct feature
        feat1_events = [e for e in iter_events if e["feature"] == "FEAT-001"]
        feat2_events = [e for e in iter_events if e["feature"] == "FEAT-002"]
        assert len(feat1_events) >= 1
        assert len(feat2_events) >= 1

    def test_feature_stall_detection_per_feature(self, tmp_path):
        """Stall detection works per-feature — stalled FEAT-001 doesn't affect FEAT-002."""
        ep = tmp_path / "events.jsonl"

        # FEAT-001: stuck (same delta 3 times)
        for i in range(4):
            emit_event(ep, make_event(
                "iteration_completed", "proj",
                feature="FEAT-001", edge="code↔unit_tests",
                iteration=i + 1, delta=2,
            ))

        # FEAT-002: converging
        for i, delta in enumerate([3, 1, 0], 1):
            emit_event(ep, make_event(
                "iteration_completed", "proj",
                feature="FEAT-002", edge="code↔unit_tests",
                iteration=i, delta=delta,
            ))

        stall_1 = sense_feature_stall(ep, "FEAT-001", threshold_iterations=3)
        stall_2 = sense_feature_stall(ep, "FEAT-002", threshold_iterations=3)

        assert stall_1.breached is True, f"FEAT-001 should be stalled: {stall_1.detail}"
        assert stall_2.breached is False, f"FEAT-002 should not be stalled: {stall_2.detail}"

    def test_concurrent_features_event_integrity(self, tmp_path):
        """After both features emit events, event log passes integrity check."""
        project = scaffold_green_project(tmp_path)
        config = make_engine_config(project, green_constraints())
        edge_config = _load_edge_config("code↔unit_tests")

        for feature_id in ["FEAT-A", "FEAT-B"]:
            iterate_edge(
                edge="code↔unit_tests",
                edge_config=edge_config,
                config=config,
                feature_id=feature_id,
                asset_content="",
            )

        ep = events_path(project)
        integrity = sense_event_log_integrity(ep)
        assert integrity.breached is False, f"Log corrupt after multi-feature: {integrity.detail}"
        # Should have events for both features (at least 2 iteration_completed)
        assert integrity.value >= 2
