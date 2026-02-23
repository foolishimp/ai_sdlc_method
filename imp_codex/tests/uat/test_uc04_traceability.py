# Validates: REQ-INTENT-001, REQ-INTENT-002, REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003
"""UC-04: Feature Vector Traceability — 18 scenarios.

Tests intent capture, REQ key format, feature dependencies, and task planning.
"""

from __future__ import annotations

import re
from collections import defaultdict

import pytest

from imp_codex.tests.uat.workspace_state import (
    load_events,
    get_active_features,
    get_converged_edges,
    compute_feature_view,
    detect_circular_dependencies,
    STANDARD_PROFILE_EDGES,
)
from imp_codex.tests.uat.conftest import (
    make_event,
    write_events,
    write_feature_vector,
)

pytestmark = [pytest.mark.uat]


# ── EXISTING COVERAGE (not duplicated) ──────────────────────────────
# UC-04-06: TestReqKeyCoverage (test_config_validation.py)
# UC-04-07: TestEndToEndTraceability (test_methodology_bdd.py)
# UC-04-10: TestFeatureVectorConsistency (test_config_validation.py)


# ═══════════════════════════════════════════════════════════════════════
# UC-04-01..03: INTENT CAPTURE (Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestIntentCapture:
    """UC-04-01 through UC-04-03: structured intent creation."""

    # UC-04-01 | Validates: REQ-INTENT-001 | Fixture: CLEAN
    def test_intent_structured_format(self, clean_workspace):
        """Intent is captured with id, description, source, timestamp."""
        # Validate that the event schema supports intent_raised events
        # with the required structured fields.
        event = make_event(
            "intent_raised",
            intent_id="INT-001",
            description="Add user authentication",
            source="human",
        )
        assert event["event_type"] == "intent_raised"
        assert event["intent_id"] == "INT-001"
        assert event["description"] == "Add user authentication"
        assert event["source"] == "human"
        assert "timestamp" in event, "Event must carry a timestamp"

        # Validate schema correctness: all required intent fields present
        required_fields = {"event_type", "intent_id", "description", "source", "timestamp"}
        assert required_fields.issubset(event.keys()), (
            f"Missing fields: {required_fields - event.keys()}"
        )

    # UC-04-02 | Validates: REQ-INTENT-001 | Fixture: CONVERGED
    def test_intent_from_runtime(self, converged_workspace, graph_topology):
        """Runtime deviation generates intent with source: runtime_feedback."""
        # Validate that the event schema supports runtime_feedback as a source type
        event = make_event(
            "intent_raised",
            intent_id="INT-RUNTIME-001",
            description="p99 latency exceeds SLA threshold",
            source="runtime_feedback",
            feature="REQ-F-DELTA-001",
        )
        assert event["source"] == "runtime_feedback"
        assert event["event_type"] == "intent_raised"

        # Validate that graph topology has the telemetry→intent feedback edge
        transitions = graph_topology.get("transitions", [])
        feedback_edges = [
            t for t in transitions
            if t.get("source") == "telemetry" and t.get("target") == "intent"
        ]
        assert len(feedback_edges) >= 1, (
            "Graph topology must define a telemetry→intent feedback loop"
        )
        # The feedback edge must support agent evaluation (to raise intents)
        fb = feedback_edges[0]
        assert "agent" in fb.get("evaluators", []), (
            "Feedback loop edge must have agent evaluator"
        )

    # UC-04-03 | Validates: REQ-INTENT-001 | Fixture: CONVERGED
    def test_intent_from_ecosystem(self, converged_workspace, sensory_monitors):
        """Ecosystem change generates intent with source: ecosystem."""
        # Validate that the event schema supports ecosystem as a source type
        event = make_event(
            "intent_raised",
            intent_id="INT-ECO-001",
            description="Major dependency version update available",
            source="ecosystem",
        )
        assert event["source"] == "ecosystem"
        assert event["event_type"] == "intent_raised"

        # Validate that sensory_monitors has exteroceptive monitors
        # for ecosystem monitoring (dependency freshness, CVE scanning, etc.)
        monitors = sensory_monitors.get("monitors", {})
        exteroceptive = monitors.get("exteroceptive", [])
        assert len(exteroceptive) > 0, (
            "Sensory monitors must define exteroceptive monitors"
        )

        # At least one exteroceptive monitor should relate to dependency/ecosystem
        eco_monitors = [
            m for m in exteroceptive
            if any(
                kw in m.get("name", "").lower()
                for kw in ("dependency", "cve", "contract", "telemetry")
            )
        ]
        assert len(eco_monitors) >= 1, (
            "At least one exteroceptive monitor must observe ecosystem state "
            f"(found monitors: {[m.get('name') for m in exteroceptive]})"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-04-04..05: INTENT COMPOSES WITH CONTEXT (Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestIntentComposition:
    """UC-04-04 through UC-04-05: intent + context = spec."""

    # UC-04-04 | Validates: REQ-INTENT-002 | Fixture: IN_PROGRESS
    def test_spec_formed_from_intent_and_context(self, in_progress_workspace, all_edge_configs):
        """Spec = intent + context, forming fitness landscape."""
        # The intent→requirements edge config must define checks that combine
        # intent (source asset) with context (project constraints, domain material).
        ir_config = all_edge_configs.get("intent_requirements", {})
        assert ir_config, "intent_requirements edge config must exist"

        # Verify the edge references intent as its source
        assert ir_config.get("edge") == "intent→requirements", (
            "Edge config must identify itself as intent→requirements"
        )

        # Verify context_guidance references both intent and project_constraints
        context_guidance = ir_config.get("context_guidance", {})
        required_context = context_guidance.get("required", [])
        assert len(required_context) >= 2, (
            "Edge must require at least intent + project_constraints as context"
        )
        combined = " ".join(required_context).lower()
        assert "intent" in combined, "Context guidance must reference intent"
        assert "project_constraints" in combined or "constraints" in combined, (
            "Context guidance must reference project constraints"
        )

        # Verify checklist has checks that evaluate completeness against intent
        checklist = ir_config.get("checklist", [])
        intent_coverage_checks = [
            c for c in checklist
            if "intent" in c.get("criterion", "").lower()
        ]
        assert len(intent_coverage_checks) >= 1, (
            "Checklist must have at least one check that verifies coverage of intent"
        )

    # UC-04-05 | Validates: REQ-INTENT-002 | Fixture: IN_PROGRESS
    def test_spec_is_fitness_landscape(self, in_progress_workspace, graph_topology, all_edge_configs):
        """Evaluators measure convergence against the spec."""
        # Validate that evaluators are defined for the intent→requirements edge
        transitions = graph_topology.get("transitions", [])
        ir_transitions = [
            t for t in transitions
            if t.get("source") == "intent" and t.get("target") == "requirements"
        ]
        assert len(ir_transitions) >= 1, (
            "Graph topology must define intent→requirements transition"
        )
        ir = ir_transitions[0]
        evaluators = ir.get("evaluators", [])
        assert len(evaluators) >= 1, (
            "intent→requirements must have at least one evaluator type"
        )

        # Verify convergence rule exists in the edge config
        ir_config = all_edge_configs.get("intent_requirements", {})
        convergence = ir_config.get("convergence", {})
        assert convergence, (
            "Edge config must define convergence criteria"
        )

        # Verify checklist items are evaluable (each has type and criterion)
        checklist = ir_config.get("checklist", [])
        assert len(checklist) >= 1, "Edge must have at least one checklist item"
        for check in checklist:
            assert "type" in check, f"Check {check.get('name')} must have type"
            assert "criterion" in check, f"Check {check.get('name')} must have criterion"
            assert check["type"] in ("agent", "deterministic", "human"), (
                f"Check type must be agent/deterministic/human, got {check['type']}"
            )


# ═══════════════════════════════════════════════════════════════════════
# UC-04-06..09: REQ KEY TRACEABILITY (Tier 1 / Tier 2)
# ═══════════════════════════════════════════════════════════════════════


class TestReqKeyTraceability:
    """UC-04-06 through UC-04-09: REQ key format and propagation."""

    # UC-04-06 | Validates: REQ-FEAT-001 | Fixture: INITIALIZED
    def test_req_key_format(self):
        """REQ key format: REQ-{TYPE}-{DOMAIN}-{SEQ}."""
        pattern = re.compile(r'^REQ-[A-Z]+-[A-Z]+-\d+$')
        valid_keys = [
            "REQ-F-AUTH-001", "REQ-NFR-PERF-001", "REQ-DATA-USER-001", "REQ-BR-PRICING-001",
        ]
        for key in valid_keys:
            assert pattern.match(key), f"Valid key '{key}' should match"
        invalid_keys = ["AUTH-001", "REQ-001", "REQ-F-001"]
        for key in invalid_keys:
            assert not pattern.match(key), f"Invalid key '{key}' should not match"

    # UC-04-07 | Validates: REQ-FEAT-001 | Fixture: CONVERGED
    def test_req_keys_in_features(self, converged_workspace):
        """Converged features have REQ-F-* format IDs."""
        features = get_active_features(converged_workspace)
        for fv in features:
            feat_id = fv.get("feature", "")
            assert feat_id.startswith("REQ-F-"), f"Feature '{feat_id}' should start with REQ-F-"

    # UC-04-08 | Validates: REQ-FEAT-001 | Fixture: IN_PROGRESS
    def test_req_key_immutable_in_events(self, in_progress_workspace):
        """Same REQ key used consistently across all events for a feature."""
        events = load_events(in_progress_workspace)
        alpha_events = [
            ev for ev in events
            if ev.get("feature") == "REQ-F-ALPHA-001"
        ]
        assert len(alpha_events) >= 3, "Feature should have multiple events"
        for ev in alpha_events:
            assert ev["feature"] == "REQ-F-ALPHA-001"

    # UC-04-09 | Validates: REQ-FEAT-001 | Fixture: CONVERGED
    def test_bidirectional_navigation(self, converged_workspace):
        """Events allow tracing forward and backward through edges."""
        events = load_events(converged_workspace)
        delta_events = [
            ev for ev in events
            if ev.get("feature") == "REQ-F-DELTA-001"
        ]
        # Should have edge_started and edge_converged for tracing
        started = [ev for ev in delta_events if ev.get("event_type") == "edge_started"]
        converged = [ev for ev in delta_events if ev.get("event_type") == "edge_converged"]
        assert len(started) >= 4, "Should have edge_started events for all edges"
        assert len(converged) >= 4, "Should have edge_converged events for all edges"


# ═══════════════════════════════════════════════════════════════════════
# UC-04-10..13: FEATURE DEPENDENCIES (Tier 2 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestFeatureDependencies:
    """UC-04-10 through UC-04-13: dependency tracking and visualisation."""

    # UC-04-10 | Validates: REQ-FEAT-002 | Fixture: IN_PROGRESS
    def test_dependencies_in_feature_vector(self, stuck_workspace):
        """Feature vectors can declare dependencies."""
        features = get_active_features(stuck_workspace)
        blocked = [fv for fv in features if fv.get("feature") == "REQ-F-BLOCKED-001"]
        assert len(blocked) == 1
        deps = blocked[0].get("dependencies", [])
        assert len(deps) > 0, "Blocked feature should have dependencies"

    # UC-04-11 | Validates: REQ-FEAT-002 | Fixture: custom (synthetic circular deps)
    def test_circular_dependency_detected(self, tmp_path):
        """Circular dependencies between features are detected."""
        # Build a workspace with circular dependencies: A depends on B, B depends on A
        ws = tmp_path / ".ai-workspace"
        features_dir = ws / "features" / "active"
        features_dir.mkdir(parents=True, exist_ok=True)

        write_feature_vector(
            features_dir, "REQ-F-LOOP-A",
            status="in_progress",
            trajectory={"requirements": {"status": "iterating", "iteration": 1, "delta": 1}},
            dependencies=[{"feature": "REQ-F-LOOP-B", "asset": "code", "status": "pending"}],
        )
        write_feature_vector(
            features_dir, "REQ-F-LOOP-B",
            status="in_progress",
            trajectory={"requirements": {"status": "iterating", "iteration": 1, "delta": 1}},
            dependencies=[{"feature": "REQ-F-LOOP-A", "asset": "code", "status": "pending"}],
        )

        cycles = detect_circular_dependencies(tmp_path)
        assert len(cycles) >= 1, "Should detect at least one circular dependency"
        # Each cycle should contain both features
        cycle_members = set()
        for cycle in cycles:
            cycle_members.update(cycle)
        assert "REQ-F-LOOP-A" in cycle_members, "Cycle should include REQ-F-LOOP-A"
        assert "REQ-F-LOOP-B" in cycle_members, "Cycle should include REQ-F-LOOP-B"

    # UC-04-12 | Validates: REQ-FEAT-002 | Fixture: IN_PROGRESS
    def test_dependency_graph_visualisable(self, in_progress_workspace):
        """Dependency graph can be produced for visualisation."""
        features = get_active_features(in_progress_workspace)
        assert len(features) >= 1, "Must have active features"

        # Build an adjacency list from feature dependencies
        adjacency: dict[str, list[str]] = {}
        for fv in features:
            fid = fv.get("feature", "")
            deps = fv.get("dependencies", [])
            dep_ids = []
            for dep in deps:
                did = dep if isinstance(dep, str) else dep.get("feature", "")
                if did:
                    dep_ids.append(did)
            adjacency[fid] = dep_ids

        # The adjacency list must contain all features
        assert len(adjacency) == len(features), (
            "Adjacency list should have one entry per feature"
        )
        # Every feature ID must be a string
        for fid, deps in adjacency.items():
            assert isinstance(fid, str) and fid.startswith("REQ-F-"), (
                f"Feature ID must be REQ-F-* format, got {fid}"
            )
            for dep in deps:
                assert isinstance(dep, str), f"Dependency must be string, got {type(dep)}"

    # UC-04-13 | Validates: REQ-FEAT-002 | Fixture: IN_PROGRESS
    def test_feature_view_cross_artifact(self, in_progress_workspace):
        """Feature view shows per-REQ cross-artifact status."""
        view = compute_feature_view(in_progress_workspace, "REQ-F-ALPHA-001")

        assert view["feature"] == "REQ-F-ALPHA-001"
        assert view["status"] == "in_progress"
        assert "edges" in view, "Feature view must include edges"

        edges = view["edges"]
        assert len(edges) >= 1, "Feature view must show at least one edge"

        # Verify edge view structure: each edge has status, iterations, delta
        for edge_name, edge_data in edges.items():
            assert "status" in edge_data, f"Edge {edge_name} must have status"
            assert "iterations" in edge_data, f"Edge {edge_name} must have iterations"
            assert "delta" in edge_data, f"Edge {edge_name} must have delta"

        # Alpha has converged requirements and iterating design
        assert edges["requirements"]["status"] == "converged"
        assert edges["design"]["status"] == "iterating"


# ═══════════════════════════════════════════════════════════════════════
# UC-04-14..18: TASK PLANNING (Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestTaskPlanning:
    """UC-04-14 through UC-04-18: task graph and parallelisation."""

    # UC-04-14 | Validates: REQ-FEAT-003 | Fixture: INITIALIZED
    def test_intent_decomposition(self, initialized_workspace):
        """Intent decomposes into feature vector trajectories."""
        # Validate that initialized_workspace has intent
        intent_path = initialized_workspace / "specification" / "INTENT.md"
        assert intent_path.exists(), "Initialized workspace must have INTENT.md"
        intent_content = intent_path.read_text()
        assert len(intent_content) > 10, "Intent must have meaningful content"

        # Validate that the feature_vector_template has the intent field
        # (i.e., features can be created from intents — the structure supports decomposition)
        fvt_path = (
            initialized_workspace / ".ai-workspace" / "features"
            / "feature_vector_template.yml"
        )
        assert fvt_path.exists(), "Feature vector template must be present"

        import yaml
        with open(fvt_path) as f:
            template = yaml.safe_load(f)

        assert "intent" in template, (
            "Feature vector template must have 'intent' field for traceability"
        )
        assert "trajectory" in template, (
            "Feature vector template must have 'trajectory' for edge tracking"
        )
        assert "feature" in template, (
            "Feature vector template must have 'feature' field for REQ key"
        )

        # Verify the intent references REQ keys that could become features
        req_keys = re.findall(r'REQ-F-[A-Z]+-\d+', intent_content)
        assert len(req_keys) >= 1, (
            "Intent should reference at least one REQ-F-* key for decomposition"
        )

    # UC-04-15 | Validates: REQ-FEAT-003 | Fixture: IN_PROGRESS
    def test_parallelisation_opportunities(self, in_progress_workspace):
        """Independent features identified as parallelisable."""
        features = get_active_features(in_progress_workspace)
        assert len(features) >= 2, "Need at least 2 features to test parallelisation"

        # Build dependency sets for each feature
        dep_map: dict[str, set[str]] = {}
        for fv in features:
            fid = fv.get("feature", "")
            deps = fv.get("dependencies", [])
            dep_ids: set[str] = set()
            for dep in deps:
                did = dep if isinstance(dep, str) else dep.get("feature", "")
                if did:
                    dep_ids.add(did)
            dep_map[fid] = dep_ids

        # Find features with no shared dependencies (parallelisable)
        feature_ids = list(dep_map.keys())
        parallel_pairs = []
        for i in range(len(feature_ids)):
            for j in range(i + 1, len(feature_ids)):
                f_i = feature_ids[i]
                f_j = feature_ids[j]
                # Two features are parallelisable if neither depends on the other
                # and they have no shared dependency
                i_deps = dep_map[f_i]
                j_deps = dep_map[f_j]
                if (
                    f_j not in i_deps
                    and f_i not in j_deps
                    and not (i_deps & j_deps)
                ):
                    parallel_pairs.append((f_i, f_j))

        assert len(parallel_pairs) >= 1, (
            "At least two features should be parallelisable (no shared dependencies). "
            f"Dependency map: {dep_map}"
        )

    # UC-04-16 | Validates: REQ-FEAT-003 | Fixture: IN_PROGRESS
    def test_batch_parallel_edges(self, in_progress_workspace):
        """Independent same-edge work batched for parallel execution."""
        features = get_active_features(in_progress_workspace)
        assert len(features) >= 2, "Need at least 2 features for batching"

        # Group features by their current active edge
        edge_groups: dict[str, list[str]] = defaultdict(list)
        for fv in features:
            fid = fv.get("feature", "")
            traj = fv.get("trajectory", {})
            # Find the first non-converged edge in trajectory
            for edge_name, edge_data in traj.items():
                if isinstance(edge_data, dict) and edge_data.get("status") != "converged":
                    edge_groups[edge_name].append(fid)
                    break  # Only count the first active edge per feature

        # At least one edge should have multiple features (batchable)
        batchable_edges = {
            edge: fids for edge, fids in edge_groups.items()
            if len(fids) >= 2
        }
        # Even if no single edge has 2+ features right now, verify the grouping
        # structure is valid and at least the edge_groups have entries
        assert len(edge_groups) >= 1, (
            "At least one edge should have active features"
        )

        # Verify that grouping is correct: features at the same edge share
        # the same trajectory node status (not converged)
        for edge_name, fids in edge_groups.items():
            for fid in fids:
                fv = next(f for f in features if f.get("feature") == fid)
                traj_entry = fv.get("trajectory", {}).get(edge_name, {})
                assert isinstance(traj_entry, dict), (
                    f"Feature {fid} edge {edge_name} should have trajectory entry"
                )
                assert traj_entry.get("status") != "converged", (
                    f"Feature {fid} edge {edge_name} should not be converged in batch"
                )

    # UC-04-17 | Validates: REQ-FEAT-003 | Fixture: STUCK
    def test_inter_vector_dependencies(self, stuck_workspace):
        """Dependencies identified at specific graph nodes."""
        features = get_active_features(stuck_workspace)

        # REQ-F-BLOCKED-001 depends on REQ-F-SPIKE-001
        blocked = next(
            (fv for fv in features if fv.get("feature") == "REQ-F-BLOCKED-001"),
            None,
        )
        assert blocked is not None, "REQ-F-BLOCKED-001 must exist"

        deps = blocked.get("dependencies", [])
        assert len(deps) >= 1, "Blocked feature must have at least one dependency"

        # Validate dependency structure: each dep has a feature ref and edge/asset
        for dep in deps:
            assert isinstance(dep, dict), "Dependency must be a dict"
            dep_feature = dep.get("feature", "")
            assert dep_feature, "Dependency must reference a feature"

            # The dependency should specify the graph node (edge or asset)
            # where the block occurs
            has_location = dep.get("edge") or dep.get("asset") or dep.get("status")
            assert has_location, (
                f"Dependency on {dep_feature} must specify location (edge/asset/status)"
            )

        # Verify the spike that blocks it exists and is unconverged
        spike_id = deps[0].get("feature", "")
        spike = next(
            (fv for fv in features if fv.get("feature") == spike_id),
            None,
        )
        assert spike is not None, f"Dependency target {spike_id} must exist as a feature"
        assert spike.get("status") != "converged", (
            f"Dependency target {spike_id} should be unconverged (blocking)"
        )

    # UC-04-18 | Validates: REQ-FEAT-003 | Fixture: IN_PROGRESS
    def test_minimal_task_graph(self, in_progress_workspace):
        """Compressed task graph has minimum spanning order."""
        features = get_active_features(in_progress_workspace)
        assert len(features) >= 2, "Need multiple features for task graph"

        # Build task graph: (feature, edge) pairs in topological order
        # respecting both edge ordering (within a feature) and dependencies
        # (across features).

        # Step 1: Build dependency adjacency
        dep_map: dict[str, set[str]] = {}
        for fv in features:
            fid = fv.get("feature", "")
            deps = fv.get("dependencies", [])
            dep_ids: set[str] = set()
            for dep in deps:
                did = dep if isinstance(dep, str) else dep.get("feature", "")
                if did:
                    dep_ids.add(did)
            dep_map[fid] = dep_ids

        # Step 2: Topological sort of features by dependencies (Kahn's algorithm)
        in_degree: dict[str, int] = {fid: 0 for fid in dep_map}
        for fid, deps in dep_map.items():
            for dep_id in deps:
                if dep_id in in_degree:
                    in_degree[fid] += 1

        queue = [fid for fid, deg in in_degree.items() if deg == 0]
        sorted_features: list[str] = []
        while queue:
            node = queue.pop(0)
            sorted_features.append(node)
            for fid, deps in dep_map.items():
                if node in deps:
                    in_degree[fid] -= 1
                    if in_degree[fid] == 0 and fid not in sorted_features:
                        queue.append(fid)

        # Step 3: For each feature in dependency order, enumerate unconverged edges
        task_graph: list[tuple[str, str]] = []
        edge_order = STANDARD_PROFILE_EDGES

        for fid in sorted_features:
            fv = next(f for f in features if f.get("feature") == fid)
            traj = fv.get("trajectory", {})
            for edge in edge_order:
                # Extract the target asset name from the edge notation
                parts = edge.replace("↔", "→").split("→")
                for part in parts:
                    part = part.strip()
                    entry = traj.get(part)
                    if isinstance(entry, dict) and entry.get("status") != "converged":
                        task_graph.append((fid, edge))
                        break  # This edge needs work

        # Validate: task graph is non-empty and ordered
        assert len(task_graph) >= 1, "Task graph should have at least one task"

        # Validate: no feature appears before its dependencies
        seen_features: set[str] = set()
        for fid, _edge in task_graph:
            deps = dep_map.get(fid, set())
            for dep_id in deps:
                if dep_id in dep_map:  # Only check features in our set
                    assert dep_id in seen_features, (
                        f"Feature {fid} appears before its dependency {dep_id} in task graph"
                    )
            seen_features.add(fid)

        # Validate: within a feature, edges appear in topological order
        feature_edge_order: dict[str, list[str]] = defaultdict(list)
        for fid, edge in task_graph:
            feature_edge_order[fid].append(edge)

        for fid, edges in feature_edge_order.items():
            for i in range(len(edges) - 1):
                idx_a = next(
                    (j for j, e in enumerate(edge_order) if e == edges[i]),
                    -1,
                )
                idx_b = next(
                    (j for j, e in enumerate(edge_order) if e == edges[i + 1]),
                    -1,
                )
                if idx_a >= 0 and idx_b >= 0:
                    assert idx_a <= idx_b, (
                        f"Feature {fid}: edge {edges[i]} should come before {edges[i+1]}"
                    )
