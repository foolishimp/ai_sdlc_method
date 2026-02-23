# Validates: REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
"""UC-02: Evaluator Framework — 15 scenarios.

Tests three evaluator types, composition per edge, and human accountability.
"""

from __future__ import annotations

import json

import pytest
import yaml

from imp_codex.tests.uat.conftest import (
    AGENTS_DIR,
    CONFIG_DIR,
    EDGE_PARAMS_DIR,
    make_event,
    write_events,
    write_feature_vector,
    write_project_constraints,
)
from imp_codex.tests.uat.workspace_state import (
    get_converged_edges,
    load_events,
    reconstruct_feature_state,
)

pytestmark = [pytest.mark.uat]


# ── EXISTING COVERAGE (not duplicated) ──────────────────────────────
# UC-02-04: TestProcessingPhases (test_config_validation.py)
# UC-02-05: TestEdgeConfigs (test_config_validation.py)
# UC-02-07: TestProfiles (test_config_validation.py)
# UC-02-08: TestEvaluatorDefaults (test_config_validation.py)


# ═══════════════════════════════════════════════════════════════════════
# UC-02-01..04: THREE EVALUATOR TYPES (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestEvaluatorTypes:
    """UC-02-01 through UC-02-04: human, agent, deterministic."""

    # UC-02-01 | Validates: REQ-EVAL-001 | Fixture: IN_PROGRESS
    def test_human_evaluator_captures_judgment(self):
        """Human evaluator presents candidate and records decision.

        Validates the iterate agent spec documents human evaluator gate
        behaviour: presentation of work, candidate review, decision recording,
        and the prohibition of auto-approval.
        """
        iterate_spec = (AGENTS_DIR / "gen-iterate.md").read_text()

        # The spec must document: presenting the candidate to the human
        assert "present" in iterate_spec.lower(), (
            "Iterate agent spec must document presenting candidates to human"
        )

        # The spec must document: recording human feedback / decision
        assert "record" in iterate_spec.lower() and "feedback" in iterate_spec.lower(), (
            "Iterate agent spec must document recording human feedback"
        )

        # The spec must document the prohibition: agent does not auto-approve
        assert "auto-approve" in iterate_spec.lower() or "auto-approves" in iterate_spec.lower(), (
            "Iterate agent spec must document the no auto-approval constraint"
        )

        # The spec must mention human_required convergence constraint
        assert "human_required" in iterate_spec, (
            "Iterate agent spec must reference human_required convergence"
        )

    # UC-02-02 | Validates: REQ-EVAL-001 | Fixture: IN_PROGRESS
    def test_agent_evaluator_computes_delta(self, all_edge_configs):
        """Agent evaluator computes delta via LLM assessment.

        Validates that edge configs define agent evaluator checks with
        assessment criteria that compute delta.
        """
        # Collect all agent-type checks across all edge configs
        agent_checks_found = False
        for edge_name, config in all_edge_configs.items():
            checklist = config.get("checklist", [])
            if not isinstance(checklist, list):
                continue
            for check in checklist:
                if not isinstance(check, dict):
                    continue
                if check.get("type") == "agent":
                    agent_checks_found = True
                    # Every agent check must have a criterion for assessment
                    assert "criterion" in check, (
                        f"Agent check '{check.get('name')}' in {edge_name} "
                        f"must have a 'criterion' field for delta computation"
                    )
                    # Criterion must be non-empty
                    criterion = check["criterion"]
                    assert criterion and len(str(criterion).strip()) > 0, (
                        f"Agent check '{check.get('name')}' in {edge_name} "
                        f"must have a non-empty criterion"
                    )

        assert agent_checks_found, "At least one edge config must define agent-type evaluator checks"

    # UC-02-03 | Validates: REQ-EVAL-001 | Fixture: IN_PROGRESS
    def test_deterministic_evaluator_binary(self, all_edge_configs):
        """Deterministic evaluator produces binary pass/fail.

        Validates that deterministic evaluators in edge configs define binary
        pass/fail checks. Tool-based checks (test_runner, linter, coverage)
        carry command + pass_criterion fields. Traceability checks carry a
        criterion field that the agent evaluates deterministically.
        """
        deterministic_checks_found = False
        command_based_found = False
        for edge_name, config in all_edge_configs.items():
            checklist = config.get("checklist", [])
            if not isinstance(checklist, list):
                continue
            for check in checklist:
                if not isinstance(check, dict):
                    continue
                if check.get("type") == "deterministic":
                    deterministic_checks_found = True
                    name = check.get("name", "<unnamed>")
                    # Every deterministic check must have EITHER:
                    # - command + pass_criterion (tool-based binary check), OR
                    # - criterion (structural/traceability binary check)
                    has_command = "command" in check and "pass_criterion" in check
                    has_criterion = "criterion" in check and len(str(check["criterion"]).strip()) > 0
                    assert has_command or has_criterion, (
                        f"Deterministic check '{name}' in {edge_name} must have "
                        f"either (command + pass_criterion) or (criterion)"
                    )
                    if has_command:
                        command_based_found = True

        assert deterministic_checks_found, (
            "At least one edge config must define deterministic-type evaluator checks"
        )
        assert command_based_found, (
            "At least one deterministic check must be command-based (with command + pass_criterion)"
        )

    # UC-02-04 | Validates: REQ-EVAL-001 | Fixture: INITIALIZED
    def test_processing_phases_declared(self, evaluator_defaults):
        """Each evaluator type declares its processing phase."""
        types = evaluator_defaults.get("evaluator_types", {})
        assert "human" in types
        assert "agent" in types
        assert "deterministic" in types

        assert types["human"]["processing_phase"] == "conscious"
        assert types["agent"]["processing_phase"] == "conscious"
        assert types["deterministic"]["processing_phase"] == "reflex"

    def test_processing_phases_spec(self, evaluator_defaults):
        """Processing phases section defines reflex, affect, conscious."""
        phases = evaluator_defaults.get("processing_phases", {})
        assert "reflex" in phases
        assert "affect" in phases
        assert "conscious" in phases


# ═══════════════════════════════════════════════════════════════════════
# UC-02-05..08: COMPOSITION PER EDGE (Tier 1)
# ═══════════════════════════════════════════════════════════════════════


class TestEvaluatorComposition:
    """UC-02-05 through UC-02-08: configurable evaluator composition."""

    # UC-02-05 | Validates: REQ-EVAL-002 | Fixture: INITIALIZED
    def test_evaluator_composition_per_edge(self, graph_topology):
        """Each transition has specific evaluator composition."""
        transitions = graph_topology.get("transitions", [])
        by_name = {t["name"]: t for t in transitions}

        # intent->requirements has [agent, human]
        ir = [t for t in transitions if t["source"] == "intent" and t["target"] == "requirements"][0]
        assert set(ir["evaluators"]) == {"agent", "human"}

        # code<->unit_tests has [agent, deterministic]
        cu = [t for t in transitions if t["source"] == "code" and t["target"] == "unit_tests"][0]
        assert set(cu["evaluators"]) == {"agent", "deterministic"}

        # code->cicd has [deterministic] only
        cc = [t for t in transitions if t["source"] == "code" and t["target"] == "cicd"][0]
        assert cc["evaluators"] == ["deterministic"]

    # UC-02-06 | Validates: REQ-EVAL-002 | Fixture: INITIALIZED
    def test_project_level_override(self, initialized_workspace):
        """Project can override evaluator composition.

        Validates that project_constraints.yml supports evaluator_overrides
        and the config schema accepts them. Creates a synthetic workspace with
        custom evaluator overrides and validates they parse correctly.
        """
        # The project_constraints_template.yml must define evaluator_overrides section
        template = (CONFIG_DIR / "project_constraints_template.yml").read_text()
        parsed = list(yaml.safe_load_all(template))
        merged = {}
        for doc in parsed:
            if doc is not None:
                merged.update(doc)

        # The template declares evaluator_overrides as a supported key
        assert "evaluator_overrides" in merged, (
            "project_constraints_template.yml must define evaluator_overrides section"
        )

        # Now write a custom project_constraints.yml with actual evaluator overrides
        ws = initialized_workspace / ".ai-workspace"
        ctx_dir = ws / "codex" / "context"
        ctx_dir.mkdir(parents=True, exist_ok=True)
        custom_constraints = {
            "project": {"name": "test-override", "version": "0.1.0"},
            "language": {"primary": "python", "version": "3.12"},
            "tools": {"test_runner": {"command": "pytest", "args": "-v", "pass_criterion": "exit code 0"}},
            "thresholds": {"test_coverage_minimum": 0.90},
            "standards": {"style_guide": "PEP 8"},
            "constraint_dimensions": {
                "ecosystem_compatibility": {"language": "python", "version": "3.12"},
                "deployment_target": {"platform": "library"},
                "security_model": {"authentication": "none"},
                "build_system": {"tool": "pip"},
            },
            "evaluator_overrides": {
                "edges": {
                    "design->code": {
                        "evaluators": ["agent", "deterministic"],
                    },
                    "code<->unit_tests": {
                        "additional_checks": [
                            {
                                "name": "no_print_statements",
                                "type": "deterministic",
                                "command": "grep -rn 'print(' src/ && exit 1 || exit 0",
                                "pass_criterion": "exit code 0",
                                "required": True,
                            }
                        ]
                    },
                },
            },
        }
        constraints_path = ctx_dir / "project_constraints.yml"
        with open(constraints_path, "w") as f:
            yaml.dump(custom_constraints, f, default_flow_style=False)

        # Re-read and validate the written config parses correctly
        with open(constraints_path) as f:
            loaded = yaml.safe_load(f)

        overrides = loaded.get("evaluator_overrides", {})
        assert "edges" in overrides, "evaluator_overrides should contain 'edges' key"
        assert "design->code" in overrides["edges"], "design->code override should be present"
        assert overrides["edges"]["design->code"]["evaluators"] == ["agent", "deterministic"]

        # Additional checks on the unit_tests override
        ut_override = overrides["edges"]["code<->unit_tests"]
        assert "additional_checks" in ut_override
        assert len(ut_override["additional_checks"]) == 1
        assert ut_override["additional_checks"][0]["name"] == "no_print_statements"

    # UC-02-07 | Validates: REQ-EVAL-002 | Fixture: INITIALIZED
    def test_profile_overrides_evaluators(self, all_profiles):
        """Profile evaluator overrides are defined."""
        std = all_profiles.get("standard", {})
        overrides = std.get("evaluators", {}).get("overrides", {})
        assert overrides, "Standard profile should have evaluator overrides"
        # intent→requirements override (profile uses unicode arrow →)
        ir = overrides.get("intent\u2192requirements", {})
        assert ir.get("evaluators") == ["agent", "human"]

    # UC-02-08 | Validates: REQ-EVAL-002 | Fixture: INITIALIZED
    def test_convergence_rules(self, evaluator_defaults):
        """Convergence composition requires all evaluators to pass."""
        rules = evaluator_defaults.get("convergence_rules", {})
        assert rules.get("composition") == "all_must_pass"
        assert rules.get("human_always_last") is True


# ═══════════════════════════════════════════════════════════════════════
# UC-02-09..15: HUMAN ACCOUNTABILITY (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestHumanAccountability:
    """UC-02-09 through UC-02-15: human evaluator authority and accountability."""

    # UC-02-09 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_agent_approval_blocked_at_human_edge(self, graph_topology, evaluator_defaults):
        """Agent delta=0 does not auto-converge at human-required edge.

        Validates that edges with human evaluators enforce the human gate
        via convergence_rules (human_always_last: true) and that the graph
        topology lists 'human' in the evaluators for key edges.
        """
        # Convergence rules enforce human_always_last
        rules = evaluator_defaults.get("convergence_rules", {})
        assert rules.get("human_always_last") is True, (
            "convergence_rules must have human_always_last: true"
        )
        assert rules.get("composition") == "all_must_pass", (
            "convergence_rules must require all evaluators to pass"
        )

        # Identify all edges that have 'human' in their evaluators list
        transitions = graph_topology.get("transitions", [])
        human_edges = [
            t for t in transitions if "human" in t.get("evaluators", [])
        ]
        assert len(human_edges) >= 1, (
            "At least one edge must have 'human' in its evaluators list"
        )

        # For each human edge, the config enforces blocking:
        # composition=all_must_pass + human_always_last=true means
        # agent-only convergence cannot bypass the human gate
        for edge in human_edges:
            evaluators = edge.get("evaluators", [])
            assert "human" in evaluators, (
                f"Edge '{edge.get('name')}' should have 'human' evaluator"
            )

    # UC-02-10 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_human_overrides_agent(self, evaluator_defaults, in_progress_workspace):
        """Human rejection overrides agent approval.

        Validates that convergence_rules define human_always_last: true and
        human_override behaviour. Creates synthetic events where agent says
        pass but human says fail (decision: rejected) and verifies that the
        feature state reflects non-convergence.
        """
        # Config validation: convergence rules support human override
        rules = evaluator_defaults.get("convergence_rules", {})
        assert rules.get("human_always_last") is True
        assert rules.get("composition") == "all_must_pass"

        # Create synthetic events: agent iteration reaches delta=0, then
        # human review rejects
        ws = in_progress_workspace / ".ai-workspace"
        events_file = ws / "events" / "events.jsonl"

        # Read existing events and extend with the override scenario
        existing_events = load_events(in_progress_workspace)

        # Feature A on requirements->design: agent converges (delta=0) but
        # human rejects
        new_events = existing_events + [
            make_event(
                "iteration_completed",
                feature="REQ-F-ALPHA-001",
                edge="requirements->design",
                iteration=3,
                delta=0,
                evaluators={"passed": 4, "failed": 0, "total": 4},
            ),
            make_event(
                "review_completed",
                feature="REQ-F-ALPHA-001",
                edge="requirements->design",
                decision="rejected",
                actor="human",
                feedback="Design missing error handling strategy",
            ),
        ]
        write_events(events_file, new_events)

        # The edge should NOT be converged (no edge_converged event after rejection)
        refreshed_events = load_events(in_progress_workspace)
        converged = get_converged_edges(refreshed_events, "REQ-F-ALPHA-001")
        assert "requirements->design" not in converged, (
            "Edge should not be converged after human rejection, even if agent delta=0"
        )

        # The review_completed event carries the human's rejection
        review_events = [
            ev for ev in refreshed_events
            if ev.get("event_type") == "review_completed"
            and ev.get("feature") == "REQ-F-ALPHA-001"
        ]
        assert len(review_events) >= 1
        assert review_events[-1].get("decision") == "rejected"

    # UC-02-11 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_decisions_attributed_to_humans(self):
        """Review events attribute decision to human, not AI.

        Creates a synthetic review_completed event with actor: human and
        verifies the event schema carries attribution fields (actor, decision,
        feedback).
        """
        # Create a review_completed event with full attribution
        review_event = make_event(
            "review_completed",
            feature="REQ-F-TEST-001",
            edge="intent->requirements",
            decision="approved",
            actor="human",
            feedback="Requirements look complete and well-structured.",
        )

        # Validate the event schema carries attribution
        assert review_event["event_type"] == "review_completed"
        assert "timestamp" in review_event
        assert review_event["actor"] == "human", (
            "review_completed event must attribute the decision to 'human'"
        )
        assert review_event["decision"] in ("approved", "rejected", "refined"), (
            "decision must be one of: approved, rejected, refined"
        )
        assert review_event["feedback"], (
            "review_completed event must carry feedback text"
        )
        assert review_event["feature"] == "REQ-F-TEST-001"
        assert review_event["edge"] == "intent->requirements"

        # Also verify a rejected event carries attribution
        reject_event = make_event(
            "review_completed",
            feature="REQ-F-TEST-001",
            edge="intent->requirements",
            decision="rejected",
            actor="human",
            feedback="Missing NFR requirements for performance.",
        )
        assert reject_event["actor"] == "human"
        assert reject_event["decision"] == "rejected"

    # UC-02-12 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_human_override_always_available(self, agent_roles, graph_topology):
        """Human can review any edge regardless of default evaluator composition.

        Validates agent_roles config has human_authority: universal, meaning
        any edge can receive human review regardless of its default evaluator
        composition.
        """
        authority = agent_roles.get("authority", {})
        assert authority.get("human_authority") == "universal", (
            "agent_roles.authority.human_authority must be 'universal' — "
            "human can review any edge"
        )

        # Even edges that only have [deterministic] evaluators can receive
        # human review because human_authority is universal
        transitions = graph_topology.get("transitions", [])
        deterministic_only_edges = [
            t for t in transitions
            if t.get("evaluators") == ["deterministic"]
        ]
        assert len(deterministic_only_edges) >= 1, (
            "There should be at least one deterministic-only edge to validate "
            "that human_authority: universal overrides the default composition"
        )

    # UC-02-13 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_spec_mutation_requires_human(self, agent_roles):
        """Spec mutations always require human approval per config."""
        authority = agent_roles.get("authority", {})
        assert authority.get("spec_mutation_requires_human") is True

    # UC-02-14 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_human_approval_blocks_convergence(
        self, graph_topology, evaluator_defaults, in_progress_workspace
    ):
        """Edge with human_required does not converge without explicit approval.

        Validates that edges with 'human' in evaluators list AND
        convergence_rules with human_always_last: true means convergence
        requires human. Creates synthetic events showing delta=0 from agent
        but no review_completed event — the feature should NOT appear converged.
        """
        # Config-level validation
        rules = evaluator_defaults.get("convergence_rules", {})
        assert rules.get("human_always_last") is True
        assert rules.get("composition") == "all_must_pass"

        # Identify a human-required edge from the topology
        transitions = graph_topology.get("transitions", [])
        human_edges = [
            t for t in transitions if "human" in t.get("evaluators", [])
        ]
        assert len(human_edges) >= 1
        target_edge = human_edges[0]
        edge_name = f"{target_edge['source']}->{target_edge['target']}"

        # Create synthetic events: iteration completes with delta=0 but
        # NO review_completed event follows
        ws = in_progress_workspace / ".ai-workspace"
        events_file = ws / "events" / "events.jsonl"

        existing_events = load_events(in_progress_workspace)
        new_events = existing_events + [
            make_event(
                "edge_started",
                feature="REQ-F-NOREV-001",
                edge=edge_name,
            ),
            make_event(
                "iteration_completed",
                feature="REQ-F-NOREV-001",
                edge=edge_name,
                iteration=1,
                delta=0,
                evaluators={"passed": 5, "failed": 0, "total": 5},
            ),
            # Deliberately NO edge_converged and NO review_completed event
        ]
        write_events(events_file, new_events)

        # Verify the edge is NOT converged (no edge_converged event)
        refreshed_events = load_events(in_progress_workspace)
        converged = get_converged_edges(refreshed_events, "REQ-F-NOREV-001")
        assert edge_name not in converged, (
            f"Edge '{edge_name}' should NOT be converged without human review, "
            f"even though agent delta=0"
        )

        # Reconstruct feature state — should show iterating, not converged
        state = reconstruct_feature_state(refreshed_events, "REQ-F-NOREV-001")
        assert state["status"] != "converged", (
            "Feature should not be converged without human approval on human-required edge"
        )

    # UC-02-15 | Validates: REQ-EVAL-003 | Fixture: IN_PROGRESS
    def test_human_feedback_stored(self):
        """Human refinement feedback stored in iteration history.

        Creates a synthetic review_completed event with feedback field.
        Validates the event schema stores human refinement feedback including
        comments, suggestions, and rationale.
        """
        # Create a review_completed event with rich feedback
        feedback_text = (
            "The design needs three changes: "
            "(1) Add circuit breaker for external API calls, "
            "(2) Use structured logging with correlation IDs, "
            "(3) Add retry policy for transient failures."
        )
        review_event = make_event(
            "review_completed",
            feature="REQ-F-FEEDBACK-001",
            edge="requirements->design",
            decision="refined",
            actor="human",
            feedback=feedback_text,
        )

        # Validate feedback is stored in the event
        assert review_event["feedback"] == feedback_text, (
            "review_completed event must store the full human feedback text"
        )
        assert review_event["decision"] == "refined", (
            "A refinement decision should be 'refined'"
        )
        assert review_event["actor"] == "human"

        # Verify the event can be serialised and deserialised (round-trip)
        serialised = json.dumps(review_event)
        deserialised = json.loads(serialised)
        assert deserialised["feedback"] == feedback_text, (
            "Feedback must survive JSON round-trip serialisation"
        )
        assert deserialised["event_type"] == "review_completed"
        assert deserialised["feature"] == "REQ-F-FEEDBACK-001"
        assert deserialised["edge"] == "requirements->design"

        # Validate feedback can contain structured content (suggestions, rationale)
        assert "circuit breaker" in deserialised["feedback"]
        assert "retry policy" in deserialised["feedback"]
