# Validates: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-001, REQ-ITER-002, REQ-ITER-003
"""UC-01: Asset Graph Engine — 23 scenarios.

Tests asset type registry, admissible transitions, Markov criteria,
universal iterate function, convergence, and functor encoding.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

from imp_codex.tests.uat.workspace_state import (
    get_converged_edges,
    load_events,
    compute_current_delta,
    get_iteration_count,
    STANDARD_PROFILE_EDGES,
)
from imp_codex.tests.uat.conftest import (
    CONFIG_DIR, PROFILES_DIR, EDGE_PARAMS_DIR, AGENTS_DIR,
    make_event, write_events, write_feature_vector,
)

pytestmark = [pytest.mark.uat]


# ── EXISTING COVERAGE (not duplicated) ──────────────────────────────
# UC-01-01: TestGraphTopology.test_has_asset_types (test_config_validation.py)
# UC-01-05: TestGraphTopology.test_feedback_loop (test_config_validation.py)
# UC-01-13: TestEdgeConfigs (test_config_validation.py)
# UC-01-19: TestFunctorEncoding (test_config_validation.py)


# ═══════════════════════════════════════════════════════════════════════
# UC-01-01..03: ASSET TYPE REGISTRY (Tier 1)
# ═══════════════════════════════════════════════════════════════════════


class TestAssetTypeRegistry:
    """UC-01-01 through UC-01-03: asset type definitions and extensibility."""

    # UC-01-01 | Validates: REQ-GRAPH-001 | Fixture: INITIALIZED
    def test_ten_asset_types(self, graph_topology):
        """Graph topology defines exactly 10 asset types."""
        types = graph_topology.get("asset_types", {})
        assert len(types) == 10, f"Expected 10 asset types, got {len(types)}: {list(types.keys())}"
        expected = {
            "intent", "requirements", "design", "code", "unit_tests",
            "test_cases", "uat_tests", "cicd", "running_system", "telemetry",
        }
        assert set(types.keys()) == expected

    def test_asset_types_have_schema(self, graph_topology):
        """Each asset type has a schema definition."""
        for name, defn in graph_topology.get("asset_types", {}).items():
            assert "schema" in defn, f"Asset type '{name}' missing schema"

    def test_asset_types_have_markov_criteria(self, graph_topology):
        """Each asset type has Markov criteria for promotion."""
        for name, defn in graph_topology.get("asset_types", {}).items():
            assert "markov_criteria" in defn, f"Asset type '{name}' missing markov_criteria"
            assert len(defn["markov_criteria"]) > 0

    # UC-01-02 | Validates: REQ-GRAPH-001 | Fixture: INITIALIZED
    def test_extensible_via_yaml(self, graph_topology):
        """Graph topology is YAML-based and therefore extensible."""
        props = graph_topology.get("graph_properties", {})
        assert props.get("extensible") is True

    # UC-01-03 | Validates: REQ-GRAPH-001 | Fixture: INITIALIZED
    def test_typed_interfaces(self, graph_topology):
        """Requirements asset type has mandatory acceptance_criteria field."""
        reqs = graph_topology["asset_types"]["requirements"]
        schema = reqs["schema"]
        assert "acceptance_criteria" in schema
        assert "has_acceptance_criteria" in reqs["markov_criteria"]


# ═══════════════════════════════════════════════════════════════════════
# UC-01-04..06: ADMISSIBLE TRANSITIONS (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestAdmissibleTransitions:
    """UC-01-04 through UC-01-06: transition enforcement and extensibility."""

    # UC-01-04 | Validates: REQ-GRAPH-002 | Fixture: INITIALIZED
    def test_non_admissible_transition_rejected(self, graph_topology):
        """Non-admissible edges (e.g., code->intent) are NOT in the transition set.

        The graph topology defines a closed set of admissible transitions.
        Any (source, target) pair not in that set is non-admissible.
        This is a config contract test -- the topology must not contain
        arbitrary back-edges that would violate the directed graph structure.
        """
        transitions = graph_topology.get("transitions", [])

        # Build the set of admissible (source, target) pairs
        admissible_pairs = {
            (t["source"], t["target"]) for t in transitions
        }

        # These non-admissible edges must NOT appear in the transition set
        non_admissible = [
            ("code", "intent"),
            ("unit_tests", "requirements"),
            ("cicd", "design"),
            ("uat_tests", "code"),
            ("running_system", "code"),
            ("telemetry", "design"),
        ]

        for source, target in non_admissible:
            assert (source, target) not in admissible_pairs, (
                f"Non-admissible edge ({source}, {target}) found in transitions"
            )

        # Also verify the transition set is exactly 10 (closed)
        assert len(transitions) == 10, (
            f"Expected exactly 10 transitions, got {len(transitions)}"
        )

    # UC-01-05 | Validates: REQ-GRAPH-002 | Fixture: INITIALIZED
    def test_feedback_loop_edge(self, graph_topology):
        """Graph has cyclic feedback loop from telemetry to intent."""
        transitions = graph_topology.get("transitions", [])
        feedback = [t for t in transitions if "Feedback" in t.get("name", "")]
        assert len(feedback) == 1
        fb = feedback[0]
        assert fb["source"] == "telemetry"
        assert fb["target"] == "intent"
        props = graph_topology.get("graph_properties", {})
        assert props.get("cyclic") is True

    # UC-01-06 | Validates: REQ-GRAPH-002 | Fixture: INITIALIZED
    def test_ten_transitions(self, graph_topology):
        """Graph topology defines exactly 10 transitions."""
        transitions = graph_topology.get("transitions", [])
        assert len(transitions) == 10

    def test_transitions_have_evaluators(self, graph_topology):
        """Every transition has evaluators defined."""
        for t in graph_topology.get("transitions", []):
            assert "evaluators" in t, f"Transition '{t['name']}' missing evaluators"
            assert len(t["evaluators"]) > 0

    def test_transitions_have_constructor(self, graph_topology):
        """Every transition has a constructor defined."""
        for t in graph_topology.get("transitions", []):
            assert "constructor" in t, f"Transition '{t['name']}' missing constructor"


# ═══════════════════════════════════════════════════════════════════════
# UC-01-07..09: MARKOV OBJECT STATUS (Tier 2 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestMarkovStatus:
    """UC-01-07 through UC-01-09: candidate vs stable asset status."""

    # UC-01-07 | Validates: REQ-GRAPH-003 | Fixture: IN_PROGRESS
    def test_non_converged_is_candidate(self, in_progress_workspace):
        """Feature B with delta>0 is a candidate, not stable."""
        events = load_events(in_progress_workspace)
        delta = compute_current_delta(events, "REQ-F-BETA-001", "code↔unit_tests")
        assert delta is not None and delta > 0, "Feature B should have delta > 0"

    # UC-01-08 | Validates: REQ-GRAPH-003 | Fixture: IN_PROGRESS
    def test_converged_is_stable(self, in_progress_workspace):
        """Feature A's converged edge has delta=0."""
        events = load_events(in_progress_workspace)
        delta = compute_current_delta(events, "REQ-F-ALPHA-001", "intent→requirements")
        assert delta == 0, "Converged edge should have delta=0"

    # UC-01-09 | Validates: REQ-GRAPH-003 | Fixture: CONVERGED
    def test_markov_usable_without_history(self, converged_workspace):
        """Converged feature assets are usable without construction history."""
        from imp_codex.tests.uat.workspace_state import get_active_features
        features = get_active_features(converged_workspace)
        for fv in features:
            assert fv["status"] == "converged"
            traj = fv.get("trajectory", {})
            for edge_name, edge_data in traj.items():
                if isinstance(edge_data, dict):
                    assert edge_data.get("status") == "converged"


# ═══════════════════════════════════════════════════════════════════════
# UC-01-10..13: UNIVERSAL ITERATE FUNCTION (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestIterateFunction:
    """UC-01-10 through UC-01-13: universal signature, parameterised, repeating."""

    # UC-01-10 | Validates: REQ-ITER-001 | Fixture: INITIALIZED
    def test_universal_signature(self, graph_topology, all_edge_configs):
        """iterate(Asset, Context[], Evaluators) is documented in the iterate agent
        spec, and all edge configs follow a consistent structural pattern
        (checklist, context_guidance, convergence).

        This validates the universal signature contract at the config level:
        the iterate agent receives (Asset, Context[], Evaluators) and every
        edge config provides the parameterisation for that signature.
        """
        # 1. Validate the iterate agent spec documents the 3-input signature
        iterate_spec = AGENTS_DIR / "gen-iterate.md"
        assert iterate_spec.exists(), "Iterate agent spec must exist"
        spec_text = iterate_spec.read_text()

        # The spec must document the three inputs
        assert "Current asset" in spec_text, (
            "Iterate agent spec must document 'Current asset' input"
        )
        assert "Context[]" in spec_text, (
            "Iterate agent spec must document 'Context[]' input"
        )
        assert "Edge parameterisation" in spec_text, (
            "Iterate agent spec must document 'Edge parameterisation' input"
        )

        # 2. Validate all edge configs follow a consistent pattern.
        #    Every edge config must have a 'convergence' section.
        #    Most have 'checklist'; cross-cutting configs like 'traceability'
        #    use layer-based keys (layer_1_*, layer_2_*, etc.) that get
        #    composed into other edges' checklists.
        for edge_name, config in all_edge_configs.items():
            assert "convergence" in config, (
                f"Edge config '{edge_name}' missing required section 'convergence'"
            )
            # Either has a 'checklist' or has layer-based checks (cross-cutting)
            has_checklist = "checklist" in config
            has_layers = any(k.startswith("layer_") for k in config)
            assert has_checklist or has_layers, (
                f"Edge config '{edge_name}' must have 'checklist' or layer-based checks"
            )

        # 3. Validate that the same agent handles all edges (not specialised agents)
        # The iterate agent spec says: "You are the SAME agent for every graph edge"
        assert "SAME agent for every graph edge" in spec_text, (
            "Iterate agent spec must assert universal agent identity"
        )

    # UC-01-11 | Validates: REQ-ITER-001 | Fixture: IN_PROGRESS
    def test_behaviour_parameterised_by_edge_config(self, all_edge_configs):
        """Edge configs exist and differ — behaviour is parameterised."""
        assert len(all_edge_configs) >= 5
        # Check that TDD config differs from intent→requirements
        tdd = all_edge_configs.get("tdd", {})
        intent_req = all_edge_configs.get("intent_requirements", {})
        assert tdd != intent_req, "Edge configs should differ between edge types"

    # UC-01-12 | Validates: REQ-ITER-001 | Fixture: IN_PROGRESS
    def test_iteration_repeats_until_convergence(self, in_progress_workspace):
        """Feature B has multiple iterations on same edge with decreasing delta."""
        events = load_events(in_progress_workspace)
        deltas = []
        for ev in events:
            if (ev.get("event_type") == "iteration_completed"
                and ev.get("feature") == "REQ-F-BETA-001"
                and ev.get("edge") == "code↔unit_tests"):
                deltas.append(ev.get("delta"))
        assert len(deltas) >= 3, "Should have 3+ iterations"
        assert deltas[-1] < deltas[0], "Delta should decrease over iterations"

    # UC-01-13 | Validates: REQ-ITER-001 | Fixture: INITIALIZED
    def test_constructor_types(self, graph_topology):
        """Different edges have different constructor types."""
        transitions = graph_topology.get("transitions", [])
        constructors = {t["name"]: t["constructor"] for t in transitions}
        assert constructors.get("Code → CI/CD") == "deterministic"
        # Most edges use agent constructor
        agent_count = sum(1 for c in constructors.values() if c == "agent")
        assert agent_count >= 6


# ═══════════════════════════════════════════════════════════════════════
# UC-01-14..18: CONVERGENCE AND PROMOTION (Tier 2 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestConvergence:
    """UC-01-14 through UC-01-18: convergence rules and promotion."""

    # UC-01-14 | Validates: REQ-ITER-002 | Fixture: IN_PROGRESS
    def test_partial_pass_not_converged(self, in_progress_workspace):
        """Feature with delta > 0 is not promoted."""
        events = load_events(in_progress_workspace)
        beta_converged = get_converged_edges(events, "REQ-F-BETA-001")
        assert "code↔unit_tests" not in beta_converged

    # UC-01-15 | Validates: REQ-ITER-002 | Fixture: INITIALIZED
    def test_configurable_threshold(self, all_profiles, evaluator_defaults):
        """Profiles can override convergence thresholds and evaluator settings.

        The standard profile defines evaluator overrides that differ from
        the evaluator defaults -- proving that profiles CAN customise
        convergence behaviour per edge.
        """
        std = all_profiles.get("standard", {})
        std_evaluators = std.get("evaluators", {})

        # Standard profile must have evaluator overrides
        overrides = std_evaluators.get("overrides", {})
        assert len(overrides) > 0, (
            "Standard profile must have evaluator overrides"
        )

        # The default evaluator set differs from the overridden edges
        default_set = std_evaluators.get("default", [])
        for edge_name, edge_override in overrides.items():
            override_evaluators = edge_override.get("evaluators", [])
            assert override_evaluators != default_set, (
                f"Override for '{edge_name}' should differ from default {default_set}"
            )

        # Full profile uses different threshold_strictness than standard
        full = all_profiles.get("full", {})
        full_convergence = full.get("convergence", {})
        std_convergence = std.get("convergence", {})
        assert full_convergence.get("threshold_strictness") != std_convergence.get("threshold_strictness"), (
            "Full and standard profiles should have different threshold_strictness"
        )
        assert full_convergence.get("human_required_on_all_edges") != std_convergence.get("human_required_on_all_edges"), (
            "Full and standard profiles should differ on human_required_on_all_edges"
        )

    # UC-01-16 | Validates: REQ-ITER-002 | Fixture: IN_PROGRESS
    def test_promotion_emits_event(self, in_progress_workspace):
        """Converged edge has edge_converged event in log."""
        events = load_events(in_progress_workspace)
        alpha_converged = get_converged_edges(events, "REQ-F-ALPHA-001")
        assert "intent→requirements" in alpha_converged

    # UC-01-17 | Validates: REQ-ITER-002 | Fixture: STUCK
    def test_stuck_detected(self, stuck_workspace):
        """Feature X with unchanged delta is detected as stuck."""
        from imp_codex.tests.uat.workspace_state import detect_stuck_features
        stuck = detect_stuck_features(stuck_workspace, threshold=3)
        stuck_features = [s["feature"] for s in stuck]
        assert "REQ-F-STUCK-001" in stuck_features

    # UC-01-18 | Validates: REQ-ITER-002 | Fixture: INITIALIZED
    def test_discovery_convergence_type(self, all_profiles):
        """Spike/discovery profiles define alternative convergence criteria
        (e.g., question_answered) distinct from the standard all_required_checks_pass.

        The spike profile uses 'question_answered_or_timeout' as its convergence
        rule, with specific conditions like 'question_answered' and
        'time_box_expired' -- proving that non-feature vector types have
        different convergence semantics.
        """
        spike = all_profiles.get("spike", {})
        assert spike, "Spike profile must exist"

        spike_convergence = spike.get("convergence", {})
        spike_rule = spike_convergence.get("rule", "")

        # Spike must NOT use the standard convergence rule
        assert spike_rule != "all_required_checks_pass", (
            "Spike profile must use a different convergence rule than standard"
        )

        # Spike must define question_answered as a convergence condition
        conditions = spike_convergence.get("conditions", [])
        assert "question_answered" in conditions, (
            "Spike profile must include 'question_answered' convergence condition"
        )
        assert "time_box_expired" in conditions, (
            "Spike profile must include 'time_box_expired' convergence condition"
        )

        # Verify standard profile uses the default rule for contrast
        std = all_profiles.get("standard", {})
        std_rule = std.get("convergence", {}).get("rule", "")
        assert std_rule == "all_required_checks_pass", (
            "Standard profile should use all_required_checks_pass"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-01-19..23: FUNCTOR ENCODING (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestFunctorEncoding:
    """UC-01-19 through UC-01-23: functor encoding in profiles and events."""

    # UC-01-19 | Validates: REQ-ITER-003 | Fixture: INITIALIZED
    def test_standard_profile_encoding(self, all_profiles):
        """Standard profile has encoding section with strategy, mode, valence."""
        std = all_profiles.get("standard", {})
        enc = std.get("encoding", {})
        assert enc.get("strategy") == "balanced"
        assert enc.get("mode") == "interactive"
        assert enc.get("valence") == "medium"

    def test_standard_profile_functional_units(self, all_profiles):
        """Standard profile defines 8 functional units with category mappings."""
        std = all_profiles.get("standard", {})
        units = std.get("encoding", {}).get("functional_units", {})
        assert len(units) == 8
        expected_units = {
            "evaluate", "construct", "classify", "route",
            "propose", "sense", "emit", "decide",
        }
        assert set(units.keys()) == expected_units

    # UC-01-20 | Validates: REQ-ITER-003 | Fixture: IN_PROGRESS
    def test_iteration_events_carry_encoding(self, tmp_path):
        """Iteration events support the encoding field in their schema.

        The iterate agent spec defines the iteration_completed event schema
        with an 'encoding' section containing strategy, mode, valence, and
        active_units.  This test creates synthetic events with encoding data
        and validates the schema contract is coherent.
        """
        ws = tmp_path / ".ai-workspace"
        events_dir = ws / "events"
        events_dir.mkdir(parents=True, exist_ok=True)

        # Create iteration_completed events WITH encoding data
        encoding_data = {
            "strategy": "balanced",
            "mode": "interactive",
            "valence": "medium",
            "active_units": {
                "evaluate": "F_D",
                "construct": "F_P",
                "classify": "F_D",
                "route": "F_H",
                "propose": "F_P",
                "sense": "F_D",
                "emit": "F_D",
                "decide": "F_H",
            },
        }

        events = [
            make_event(
                "iteration_completed",
                feature="REQ-F-TEST-001",
                edge="intent→requirements",
                iteration=1,
                delta=3,
                encoding=encoding_data,
            ),
            make_event(
                "iteration_completed",
                feature="REQ-F-TEST-001",
                edge="intent→requirements",
                iteration=2,
                delta=1,
                encoding=encoding_data,
            ),
        ]
        write_events(events_dir / "events.jsonl", events)

        # Read back and validate encoding field survives round-trip
        loaded = load_events(tmp_path)
        assert len(loaded) == 2

        for ev in loaded:
            assert "encoding" in ev, "Event must carry encoding field"
            enc = ev["encoding"]
            assert enc["strategy"] == "balanced"
            assert enc["mode"] == "interactive"
            assert enc["valence"] == "medium"
            assert "active_units" in enc
            assert enc["active_units"]["evaluate"] == "F_D"
            assert enc["active_units"]["decide"] == "F_H"

    # UC-01-21 | Validates: REQ-ITER-003 | Fixture: INITIALIZED
    def test_category_fixed_units(self, all_profiles):
        """Category-fixed units (emit, decide) have consistent categories across profiles."""
        for profile_name, profile in all_profiles.items():
            enc = profile.get("encoding", {})
            units = enc.get("functional_units", {})
            if not units:
                continue
            if "emit" in units:
                assert units["emit"] == "F_D", (
                    f"Profile '{profile_name}': emit must be F_D, got {units['emit']}"
                )
            if "decide" in units:
                assert units["decide"] == "F_H", (
                    f"Profile '{profile_name}': decide must be F_H, got {units['decide']}"
                )

    # UC-01-22 | Validates: REQ-ITER-003 | Fixture: INITIALIZED
    def test_encoding_escalation_event(self, affect_triage):
        """The affect_triage config and event schema define an encoding escalation
        pathway.

        The iterate agent spec documents the 'encoding_escalated' event type
        (emitted when a functional unit's encoding changes via natural
        transformation eta).  This test validates that:
        1. The affect_triage classification rules can handle encoding signals
           (the agent_fallback rule catches unmatched signals).
        2. The escalation thresholds exist per profile for routing decisions.
        3. The encoding_escalated event schema is well-defined in the spec.
        """
        # 1. Validate the affect_triage has classification rules
        rules = affect_triage.get("classification_rules", [])
        assert len(rules) > 0, "Affect triage must have classification rules"

        # The agent_fallback rule catches signals not matched by explicit rules,
        # including encoding-related signals
        fallback_rules = [r for r in rules if r.get("name") == "agent_fallback"]
        assert len(fallback_rules) == 1, (
            "Must have an agent_fallback rule for unmatched signals"
        )
        assert fallback_rules[0].get("classification") == "agent_classify", (
            "Fallback must route to agent classification"
        )

        # 2. Validate escalation thresholds exist per profile
        thresholds = affect_triage.get("escalation_thresholds", {})
        assert "standard" in thresholds, "Must have standard profile threshold"
        assert "spike" in thresholds, "Must have spike profile threshold"
        assert "full" in thresholds, "Must have full profile threshold"

        # 3. Validate the encoding_escalated event is documented in the iterate spec
        iterate_spec = AGENTS_DIR / "gen-iterate.md"
        spec_text = iterate_spec.read_text()
        assert "encoding_escalated" in spec_text, (
            "Iterate agent spec must document encoding_escalated event type"
        )
        # The spec documents the event schema fields
        assert "functional_unit" in spec_text
        assert "from_category" in spec_text
        assert "to_category" in spec_text

    # UC-01-23 | Validates: REQ-ITER-003 | Fixture: INITIALIZED
    def test_escalation_trajectory_recorded(self, tmp_path):
        """Feature vector template supports escalation history in trajectory entries.

        The feature_vector_template.yml defines trajectory entries with an
        'escalations' list field.  This test validates that:
        1. The template defines the escalations field.
        2. A synthetic feature vector can store escalation entries.
        3. The escalation entries round-trip through YAML correctly.
        """
        # 1. Validate the feature_vector_template has escalations in trajectory
        template_path = CONFIG_DIR / "feature_vector_template.yml"
        assert template_path.exists(), "Feature vector template must exist"
        template_text = template_path.read_text()
        with open(template_path) as f:
            template = yaml.safe_load(f)

        # The template trajectory entries must have 'escalations' field
        traj = template.get("trajectory", {})
        assert traj, "Template must have trajectory section"
        for edge_name, edge_data in traj.items():
            if isinstance(edge_data, dict):
                assert "escalations" in edge_data, (
                    f"Trajectory edge '{edge_name}' must have 'escalations' field"
                )

        # 2. Create a feature vector with escalation history
        ws = tmp_path / ".ai-workspace"
        features_dir = ws / "features" / "active"

        escalation_entries = [
            {
                "iteration": 3,
                "functional_unit": "evaluate",
                "from": "F_D",
                "to": "F_H",
                "trigger": "deterministic evaluator insufficient for ambiguous requirement",
                "timestamp": "2026-02-22T10:00:00Z",
            },
            {
                "iteration": 5,
                "functional_unit": "construct",
                "from": "F_P",
                "to": "F_H",
                "trigger": "agent-generated code failed 3 consecutive iterations",
                "timestamp": "2026-02-22T11:00:00Z",
            },
        ]

        fv_path = write_feature_vector(
            features_dir, "REQ-F-ESC-001",
            status="in_progress",
            trajectory={
                "requirements": {
                    "status": "converged",
                    "escalations": [],
                },
                "design": {
                    "status": "iterating",
                    "iteration": 5,
                    "delta": 1,
                    "escalations": escalation_entries,
                },
            },
        )

        # 3. Read back and validate escalation entries survive round-trip
        with open(fv_path) as f:
            loaded = yaml.safe_load(f)

        traj = loaded["trajectory"]
        design_escalations = traj["design"]["escalations"]
        assert len(design_escalations) == 2, (
            f"Expected 2 escalation entries, got {len(design_escalations)}"
        )

        esc1 = design_escalations[0]
        assert esc1["iteration"] == 3
        assert esc1["functional_unit"] == "evaluate"
        assert esc1["from"] == "F_D"
        assert esc1["to"] == "F_H"
        assert "trigger" in esc1
        assert "timestamp" in esc1

        esc2 = design_escalations[1]
        assert esc2["iteration"] == 5
        assert esc2["functional_unit"] == "construct"

        # Requirements edge has empty escalations (no escalations occurred)
        req_escalations = traj["requirements"]["escalations"]
        assert req_escalations == [], "Requirements edge should have empty escalations"
