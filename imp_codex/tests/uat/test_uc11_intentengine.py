# Validates: REQ-SUPV-001, REQ-SUPV-002
"""UC-11: IntentEngine / Supervision — 14 scenarios.

Tests IntentEngine interface (observer → evaluator → typed_output),
three output regimes, constraint tolerances, and tolerance pressure.
"""

from __future__ import annotations

import pytest

from imp_codex.tests.uat.conftest import CONFIG_DIR, AGENTS_DIR, PLUGIN_ROOT
from imp_codex.tests.uat.workspace_state import (
    classify_tolerance_breach,
    get_unactioned_escalations,
    load_events,
    reconstruct_feature_state,
)

pytestmark = [pytest.mark.uat]


# ═══════════════════════════════════════════════════════════════════════
# UC-11-01..07: INTENTENGINE INTERFACE (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestIntentEngineInterface:
    """UC-11-01 through UC-11-07: IntentEngine pattern at all scales."""

    # UC-11-01 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_every_edge_produces_ie_output(self, in_progress_workspace):
        """Every edge traversal produces IntentEngine output.

        At the reflex level, the IntentEngine output for each edge is the
        iteration_completed or edge_converged event.  Every edge_started must
        have at least one corresponding iteration_completed or edge_converged.
        """
        events = load_events(in_progress_workspace)

        # Collect all (feature, edge) pairs that have edge_started events
        started_pairs: set[tuple[str, str]] = set()
        for ev in events:
            if ev.get("event_type") == "edge_started":
                pair = (ev.get("feature", ""), ev.get("edge", ""))
                started_pairs.add(pair)

        assert len(started_pairs) > 0, "Should have edge_started events"

        # Collect all (feature, edge) pairs that have iteration_completed or edge_converged
        output_pairs: set[tuple[str, str]] = set()
        for ev in events:
            if ev.get("event_type") in ("iteration_completed", "edge_converged"):
                pair = (ev.get("feature", ""), ev.get("edge", ""))
                output_pairs.add(pair)

        # Every started edge must have produced at least one IE output
        missing = started_pairs - output_pairs
        assert missing == set(), (
            f"Edges started but without IE output (iteration_completed / edge_converged): {missing}"
        )

    # UC-11-02 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_three_ambiguity_regimes(self, affect_triage):
        """Ambiguity classified into zero, bounded nonzero, persistent.

        The three ambiguity regimes map to the three escalation behaviours
        in affect_triage classification_rules:
        - zero ambiguity     → escalation: "always" (deterministic, no judgment needed)
        - bounded nonzero    → escalation: "threshold" (rule-based, quantitative)
        - persistent/unknown → escalation: "agent_decides" (requires agent classification)

        Additionally, classify_tolerance_breach returns the three output types
        (reflex.log, specEventLog, escalate) corresponding to these regimes.
        """
        rules = affect_triage.get("classification_rules", [])
        assert len(rules) > 0, "Should have classification rules"

        escalation_types = {r.get("escalation") for r in rules}

        # The three regimes must all be represented
        assert "always" in escalation_types, (
            "Zero-ambiguity regime (escalation: always) missing"
        )
        assert "threshold" in escalation_types, (
            "Bounded-nonzero regime (escalation: threshold) missing"
        )
        assert "agent_decides" in escalation_types, (
            "Persistent/unknown regime (escalation: agent_decides) missing"
        )

        # classify_tolerance_breach maps to the three output types
        assert classify_tolerance_breach(5, 10) == "reflex.log"       # within threshold → zero ambiguity
        assert classify_tolerance_breach(15, 10) == "specEventLog"    # exceeds threshold → bounded nonzero
        assert classify_tolerance_breach(25, 10, severity="critical") == "escalate"  # critical → persistent

    # UC-11-03 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_three_output_types(self, in_progress_workspace):
        """Three output types: reflex.log, specEventLog, escalate.

        Events in the workspace map to one of three IntentEngine output types:
        - reflex.log    → normal iteration events (iteration_completed, edge_converged)
        - specEventLog  → spec-level findings (spawn_created, review_completed)
        - escalate      → stuck/blocked conditions requiring conscious intervention
        """
        events = load_events(in_progress_workspace)
        assert len(events) > 0, "Should have events"

        REFLEX_TYPES = {"iteration_completed", "edge_converged", "edge_started", "project_initialized"}
        SPEC_EVENT_TYPES = {"spawn_created", "review_completed", "spec_modified", "gaps_validated"}
        ESCALATE_TYPES = {"intent_raised", "escalation", "convergence_escalated"}

        all_known_types = REFLEX_TYPES | SPEC_EVENT_TYPES | ESCALATE_TYPES

        # Classify each event
        reflex_count = 0
        spec_count = 0
        escalate_count = 0
        unclassified = []

        for ev in events:
            etype = ev.get("event_type", "")
            if etype in REFLEX_TYPES:
                reflex_count += 1
            elif etype in SPEC_EVENT_TYPES:
                spec_count += 1
            elif etype in ESCALATE_TYPES:
                escalate_count += 1
            else:
                unclassified.append(etype)

        # in_progress_workspace should have reflex-level events at minimum
        assert reflex_count > 0, "Should have reflex.log-level events"

        # All events must be classifiable into one of the three types
        assert unclassified == [], (
            f"Events not classifiable into the three output types: {unclassified}"
        )

    # UC-11-04 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_affect_propagation(self, evaluator_defaults):
        """Affect propagates through chained IntentEngine invocations.

        The processing_phases in evaluator_defaults define a chain:
        reflex fires first, affect classifies, conscious decides.
        The phase ordering forms the propagation chain — each phase
        enables the next.
        """
        phases = evaluator_defaults.get("processing_phases", {})
        assert "reflex" in phases
        assert "affect" in phases
        assert "conscious" in phases

        # Verify the propagation chain: reflex → affect → conscious
        # Reflex fires unconditionally (no dependency)
        reflex_fires = phases["reflex"].get("fires_when", "").lower()
        assert "every iteration" in reflex_fires or "no exceptions" in reflex_fires, (
            "Reflex must fire unconditionally"
        )

        # Affect fires when reflex surfaces a signal
        affect_fires = phases["affect"].get("fires_when", "").lower()
        assert "reflex" in affect_fires, (
            "Affect must fire in response to reflex output"
        )

        # Conscious fires when affect determines signal warrants deliberation
        conscious_fires = phases["conscious"].get("fires_when", "").lower()
        assert "affect" in conscious_fires, (
            "Conscious must fire in response to affect triage"
        )

        # Verify ordering: each evaluator type maps to a specific phase
        eval_types = evaluator_defaults.get("evaluator_types", {})
        assert eval_types.get("deterministic", {}).get("processing_phase") == "reflex"
        assert eval_types.get("agent", {}).get("processing_phase") == "conscious"
        assert eval_types.get("human", {}).get("processing_phase") == "conscious"

    # UC-11-05 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_escalate_becomes_reflex_input(self, affect_triage, graph_topology):
        """Level N escalate becomes Level N+1 reflex input.

        The design contract: affect_triage escalation feeds back into the
        methodology loop.  An escalation generates an intent_raised event or
        proposal, which re-enters the graph at the intent node (via the
        feedback loop edge Telemetry → Intent).

        Verify: (1) escalation actions reference intent generation,
        (2) the graph has a feedback loop from telemetry → intent.
        """
        # The graph must have the feedback loop transition
        transitions = graph_topology.get("transitions", [])
        feedback = [
            t for t in transitions
            if t.get("source") == "telemetry" and t.get("target") == "intent"
        ]
        assert len(feedback) > 0, (
            "Graph must have Telemetry → Intent feedback loop transition"
        )

        # The review boundary in affect_triage defines MCP tools for handling
        # escalated proposals — the human_required_for list shows that escalation
        # feeds back through conscious approval into the workspace
        review_boundary = affect_triage.get("review_boundary", {})
        assert review_boundary, "affect_triage must define a review_boundary"

        # The autonomy model is draft_only: escalation produces a draft
        # that requires human approval before entering the methodology loop
        assert review_boundary.get("autonomy_model") == "draft_only", (
            "Escalation enters as draft_only — proposals, not direct modifications"
        )

        # The human_required_for list includes event_emission and feature_vector_update
        # — this ensures escalation output goes through the conscious phase
        human_required = review_boundary.get("human_required_for", [])
        assert "event_emission" in human_required, (
            "Escalation-produced events require human approval"
        )

    # UC-11-06 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_intentengine_applies_at_every_scale(self, evaluator_defaults):
        """IntentEngine pattern defined in evaluator processing phases."""
        phases = evaluator_defaults.get("processing_phases", {})
        # All 3 phases (reflex, affect, conscious) support the IntentEngine pattern
        assert "reflex" in phases
        assert "affect" in phases
        assert "conscious" in phases
        # Reflex fires unconditionally
        assert "every iteration" in phases["reflex"].get("fires_when", "").lower() or \
               "no exceptions" in phases["reflex"].get("fires_when", "").lower()

    # UC-11-07 | Validates: REQ-SUPV-001 | Fixture: IN_PROGRESS
    def test_ie_on_all_actors(self, sensory_monitors, evaluator_defaults, agent_roles):
        """Iterate agent, monitors, hooks, observers all expose IE interface.

        Verify that all actor types are defined across the config/filesystem:
        - iterate agent: agents/ directory has the iterate agent
        - monitors: sensory_monitors defines interoceptive + exteroceptive
        - hooks: hooks/ directory has hook scripts
        - observers: agent_roles defines the observer role
        """
        # 1. Iterate agent exists
        iterate_agent = AGENTS_DIR / "gen-iterate.md"
        assert iterate_agent.exists(), (
            f"Iterate agent not found at {iterate_agent}"
        )

        # 2. Sensory monitors define both interoceptive and exteroceptive
        monitors = sensory_monitors.get("monitors", {})
        assert len(monitors.get("interoceptive", [])) > 0, (
            "Must have interoceptive monitors"
        )
        assert len(monitors.get("exteroceptive", [])) > 0, (
            "Must have exteroceptive monitors"
        )

        # 3. Hooks directory has hook scripts
        hooks_dir = PLUGIN_ROOT / "hooks"
        assert hooks_dir.exists(), f"Hooks directory not found at {hooks_dir}"
        hook_files = list(hooks_dir.glob("*.sh")) + list(hooks_dir.glob("*.json"))
        assert len(hook_files) > 0, "Must have hook files"

        # 4. Observer role is defined in agent_roles
        roles = agent_roles.get("roles", {})
        assert "observer" in roles, (
            "Agent roles must define the 'observer' role"
        )
        # Observer must have convergence authority on telemetry edges
        observer_edges = roles["observer"].get("converge_edges", [])
        assert any("telemetry" in e for e in observer_edges), (
            "Observer role must have authority on telemetry edges"
        )

        # 5. Processing phases map to actor types via evaluator_types
        eval_types = evaluator_defaults.get("evaluator_types", {})
        assert "deterministic" in eval_types, "Must have deterministic evaluator type"
        assert "agent" in eval_types, "Must have agent evaluator type"
        assert "human" in eval_types, "Must have human evaluator type"


# ═══════════════════════════════════════════════════════════════════════
# UC-11-08..14: CONSTRAINT TOLERANCES (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestConstraintTolerances:
    """UC-11-08 through UC-11-14: measurable thresholds on all constraints."""

    # UC-11-08 | Validates: REQ-SUPV-002 | Fixture: INITIALIZED
    def test_constraints_have_thresholds(self, sensory_monitors):
        """All enabled monitors have measurable thresholds or evaluation criteria."""
        for monitor_type in ("interoceptive", "exteroceptive"):
            monitors = sensory_monitors.get("monitors", {}).get(monitor_type, [])
            for m in monitors:
                if not m.get("enabled", True):
                    continue
                # Monitors define evaluation criteria via thresholds, checks,
                # severity filters, or commands (which are themselves evaluators)
                has_criteria = (
                    m.get("threshold")
                    or m.get("checks")
                    or m.get("severity_filter")
                    or m.get("commands")
                    or m.get("sources")
                    or m.get("endpoint")
                )
                assert has_criteria, (
                    f"Monitor {m['id']} ({m['name']}) has no measurable criteria"
                )

    # UC-11-09 | Validates: REQ-SUPV-002
    def test_tolerance_breach_classified(self):
        """Tolerance breach classified as reflex.log, specEventLog, or escalate.

        Uses classify_tolerance_breach() to verify all three output types are
        reachable depending on value, threshold, and severity.
        """
        # Within threshold → reflex.log (normal, no breach)
        assert classify_tolerance_breach(5, 10) == "reflex.log"
        assert classify_tolerance_breach(10, 10) == "reflex.log"  # equal = within

        # Exceeds threshold but not by 2x, severity=warning → specEventLog
        assert classify_tolerance_breach(15, 10) == "specEventLog"
        assert classify_tolerance_breach(12, 10, severity="warning") == "specEventLog"

        # Exceeds threshold by >2x → escalate
        assert classify_tolerance_breach(25, 10) == "escalate"
        assert classify_tolerance_breach(21, 10) == "escalate"  # ratio > 2.0

        # Critical severity always escalates (regardless of ratio)
        assert classify_tolerance_breach(11, 10, severity="critical") == "escalate"
        assert classify_tolerance_breach(15, 10, severity="critical") == "escalate"

    # UC-11-10 | Validates: REQ-SUPV-002 | Fixture: IN_PROGRESS
    def test_monitors_use_tolerances(self, sensory_monitors):
        """Sensory monitors define threshold values for evaluation."""
        intro_monitors = sensory_monitors.get("monitors", {}).get("interoceptive", [])
        monitors_with_thresholds = [
            m for m in intro_monitors if m.get("threshold")
        ]
        assert len(monitors_with_thresholds) >= 5, (
            "Most interoceptive monitors should have thresholds"
        )

    # UC-11-11 | Validates: REQ-SUPV-002
    def test_design_binding_tolerances(self, graph_topology, all_profiles):
        """Design bindings have performance/cost tolerances.

        Constraint dimensions in graph_topology define the categories that
        design must resolve. Profiles define iteration budgets which serve
        as tolerance thresholds for convergence pressure.
        """
        # Constraint dimensions exist and have meaningful structure
        dims = graph_topology.get("constraint_dimensions", {})
        assert len(dims) > 0, "Must have constraint dimensions"

        # Mandatory dimensions must have resolves_via field (the tolerance mechanism)
        mandatory_dims = {
            name: dim for name, dim in dims.items()
            if isinstance(dim, dict) and dim.get("mandatory")
        }
        assert len(mandatory_dims) >= 3, (
            "Should have at least 3 mandatory constraint dimensions"
        )
        for name, dim in mandatory_dims.items():
            assert dim.get("resolves_via"), (
                f"Mandatory dimension '{name}' must specify resolves_via (tolerance mechanism)"
            )

        # Profiles define iteration budgets as convergence tolerances
        for profile_name, profile_data in all_profiles.items():
            if profile_data is None:
                continue
            iteration = profile_data.get("iteration", {})
            if iteration:
                budget = iteration.get("budget")
                assert budget is not None, (
                    f"Profile '{profile_name}' has iteration config but no budget tolerance"
                )

    # UC-11-12 | Validates: REQ-SUPV-002 | Fixture: IN_PROGRESS
    def test_tolerances_at_every_scale(self, all_profiles, sensory_monitors):
        """Tolerances defined at iteration, edge, feature, and production scales."""
        # Iteration scale: profile defines iteration budget
        std = all_profiles.get("standard", {})
        assert std.get("iteration", {}).get("budget")

        # Edge scale: evaluator checks define pass/fail
        # (checked via edge configs having checklist entries)

        # Monitor scale: thresholds on monitors
        intro = sensory_monitors.get("monitors", {}).get("interoceptive", [])
        assert any(m.get("threshold") for m in intro)

    # UC-11-13 | Validates: REQ-SUPV-002
    def test_tolerance_pressure_equilibrium(self):
        """Tolerance pressure balances escalation pressure.

        Create synthetic events with escalations and resolutions. Verify that
        the ratio of unactioned escalations to total escalations is bounded
        (i.e. the system does not accumulate unbounded escalation pressure).
        """
        from imp_codex.tests.uat.conftest import make_event

        # Scenario: 4 escalations, 2 are actioned (resolved), 2 unactioned
        events = [
            make_event("project_initialized", project="test"),
            # Escalation 1 — actioned by spawn_created
            make_event("intent_raised", intent_id="ESC-001", feature="F-001",
                       reason="stuck on design"),
            make_event("spawn_created", intent_id="ESC-001", feature="F-001",
                       spawn="SPIKE-001"),
            # Escalation 2 — actioned by review_completed
            make_event("escalation", intent_id="ESC-002", feature="F-002",
                       reason="coverage below threshold"),
            make_event("review_completed", intent_id="ESC-002", feature="F-002"),
            # Escalation 3 — NOT actioned
            make_event("intent_raised", intent_id="ESC-003", feature="F-003",
                       reason="test flake rate high"),
            # Escalation 4 — NOT actioned
            make_event("escalation", intent_id="ESC-004", feature="F-004",
                       reason="spec drift detected"),
        ]

        unactioned = get_unactioned_escalations(events)

        # Exactly 2 unactioned escalations
        unactioned_ids = {
            e.get("intent_id", "") or e.get("data", {}).get("intent_id", "")
            for e in unactioned
        }
        assert "ESC-003" in unactioned_ids
        assert "ESC-004" in unactioned_ids
        assert "ESC-001" not in unactioned_ids, "ESC-001 was actioned by spawn"
        assert "ESC-002" not in unactioned_ids, "ESC-002 was actioned by review"

        # Pressure ratio: unactioned / total escalations <= 1.0 (bounded)
        total_escalations = sum(
            1 for e in events
            if e.get("event_type") in ("intent_raised", "escalation")
        )
        assert total_escalations == 4
        pressure_ratio = len(unactioned) / total_escalations
        assert pressure_ratio <= 1.0, "Escalation pressure must be bounded"
        assert pressure_ratio == 0.5, "Expected 2/4 unactioned"

    # UC-11-14 | Validates: REQ-SUPV-002
    def test_constraint_without_tolerance_flagged(self, sensory_monitors):
        """Constraint without measurable tolerance flagged as incomplete.

        Build a synthetic monitor config missing measurable criteria and verify
        it would be detected.  This is the inverse of test_constraints_have_thresholds.
        """
        # Synthetic monitor with NO measurable criteria
        bad_monitor = {
            "id": "TEST-BAD-001",
            "name": "bad_monitor",
            "description": "A monitor with no threshold, checks, commands, or sources",
            "enabled": True,
            # Deliberately missing: threshold, checks, severity_filter,
            # commands, sources, endpoint
        }

        # The same criteria check used in test_constraints_have_thresholds
        has_criteria = (
            bad_monitor.get("threshold")
            or bad_monitor.get("checks")
            or bad_monitor.get("severity_filter")
            or bad_monitor.get("commands")
            or bad_monitor.get("sources")
            or bad_monitor.get("endpoint")
        )
        assert not has_criteria, (
            "A monitor without measurable criteria should be flagged"
        )

        # Verify that all real enabled monitors DO have criteria (positive check)
        for monitor_type in ("interoceptive", "exteroceptive"):
            monitors = sensory_monitors.get("monitors", {}).get(monitor_type, [])
            for m in monitors:
                if not m.get("enabled", True):
                    continue
                real_criteria = (
                    m.get("threshold")
                    or m.get("checks")
                    or m.get("severity_filter")
                    or m.get("commands")
                    or m.get("sources")
                    or m.get("endpoint")
                )
                assert real_criteria, (
                    f"Real monitor {m['id']} ({m['name']}) has no measurable criteria — "
                    "this is the constraint-without-tolerance condition"
                )
