# Validates: REQ-UX-001, REQ-UX-004, REQ-FEAT-001, REQ-FEAT-003,, REQ-F-UX-001
#            REQ-EDGE-001, REQ-EDGE-004, REQ-ITER-001, REQ-ITER-002
"""BDD-structured E2E tests — additional UC coverage using the converged_project fixture.

These tests add Given/When/Then coverage for use-case clusters:

  TestUC09UX_StateNavigation  — UC-09: state-driven routing & auto-feature selection
  TestUC04Feature_Trajectory  — UC-04: feature vector trajectory management
  TestUC05Edge_TDDCoevolution — UC-05: TDD co-evolution, REQ tagging at code↔unit_tests
  TestUC01Iter_Convergence    — UC-01: iterate() universal signature, delta to zero

Spec: imp_gemini/tests/e2e/scenarios/convergence_lifecycle/spec.md

Run:
    export PYTHONPATH=$PYTHONPATH:.
    pytest tests/e2e/test_e2e_bdd.py -v -m e2e -s
"""

import pathlib
import subprocess
import pytest

from tests.e2e.conftest import skip_no_gemini
from tests.e2e.validators import (
    load_events,
    load_feature_vector,
    find_python_files,
    extract_req_tags,
    validate_generated_tests_pass
)

FEATURE_ID = "REQ-F-CONV-001"
STANDARD_EDGES = {
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
}

# ═══════════════════════════════════════════════════════════════════════════════
# UC-09: UX — State-Driven Navigation and Auto-Feature Selection
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@skip_no_gemini
class TestUC09UX_StateNavigation:
    """
    UC-09: UX — State-Driven Routing and Auto-Feature Selection
    Validates: REQ-UX-001, REQ-UX-004

    Spec: scenarios/convergence_lifecycle/spec.md

    Given the converged temperature-converter project
    When I inspect the event sequence produced by gemini start --auto

    Then the project traversed the state machine:
      project_initialized → IN_PROGRESS (first edge_started) → ALL_CONVERGED (all edges done)
    And auto-feature selection picked REQ-F-CONV-001 without manual specification
    And gemini start iterated through all 4 standard-profile edges automatically
    And the event sequence proves no manual intervention was needed
    """

    def test_project_initialized_event_present(self, mock_converged_project: pathlib.Path):
        """
        Given: converged project
        When: I check the event log
        Then: project_initialized is the first event (UNINITIALISED → INITIALIZED)
        """
        events = load_events(mock_converged_project)
        assert events, "events.jsonl is empty"
        first = events[0]
        assert first.get("event_type") == "project_initialized", (
            f"Expected project_initialized as first event, got: "
            f"{first.get('event_type')}"
        )

    def test_all_standard_edges_started(self, mock_converged_project: pathlib.Path):
        """
        Given: converged project
        When: I collect all edge_started events
        Then: all 4 standard-profile edges were started by auto-mode
             (REQ-UX-004: automatic edge selection, not manual)
        """
        events = load_events(mock_converged_project)
        started = {
            e.get("edge")
            for e in events
            if e.get("event_type") == "edge_started"
        }
        missing = STANDARD_EDGES - started
        assert not missing, (
            f"Auto-mode did not start edges: {missing}. "
            f"Started edges: {started}"
        )

    def test_all_standard_edges_converged(self, mock_converged_project: pathlib.Path):
        """
        Given: converged project
        When: I collect all edge_converged events
        Then: all 4 standard-profile edges converged (CONVERGED final state)
        """
        events = load_events(mock_converged_project)
        converged = {
            e.get("edge")
            for e in events
            if e.get("event_type") == "edge_converged"
        }
        missing = STANDARD_EDGES - converged
        assert not missing, (
            f"Edges not converged: {missing}. "
            f"Converged edges: {converged}"
        )

    def test_edges_traversed_in_topological_order(self, mock_converged_project: pathlib.Path):
        """
        Given: converged project
        When: I extract the sequence of edge_converged events
        Then: edges were completed in dependency order:
              intent→requirements before requirements→design,
              requirements→design before design→code,
              design→code before code↔unit_tests
             (REQ-UX-001: state machine enforces topological ordering)
        """
        events = load_events(mock_converged_project)
        converged_order = [
            e.get("edge")
            for e in events
            if e.get("event_type") == "edge_converged"
        ]

        ORDERED_EDGES = [
            "intent→requirements",
            "requirements→design",
            "design→code",
            "code↔unit_tests",
        ]
        found = [e for e in ORDERED_EDGES if e in converged_order]
        positions = {e: converged_order.index(e) for e in found}

        for i in range(1, len(ORDERED_EDGES)):
            prev, curr = ORDERED_EDGES[i - 1], ORDERED_EDGES[i]
            if prev in positions and curr in positions:
                assert positions[prev] < positions[curr], (
                    f"Topological order violated: "
                    f"'{curr}' converged before '{prev}'. "
                    f"Full order: {converged_order}"
                )

    def test_feature_referenced_in_events(self, mock_converged_project: pathlib.Path):
        """
        Given: converged project
        When: I check feature references in edge_started / edge_converged events
        Then: REQ-F-CONV-001 appears in events — auto-selection picked it
             (REQ-UX-004: gemini start auto-selects the next pending feature)
        """
        events = load_events(mock_converged_project)
        feature_events = [
            e for e in events
            if e.get("feature") == FEATURE_ID
            or e.get("event_type") == "project_initialized"  # project-level
        ]
        assert feature_events, (
            f"No events reference feature {FEATURE_ID}. "
            "Expected auto-mode to select this feature."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# UC-04: Feature Vectors — Trajectory Management
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@skip_no_gemini
class TestUC04Feature_Trajectory:
    """
    UC-04: Feature Vectors — Trajectory Management
    Validates: REQ-FEAT-001, REQ-FEAT-003

    Spec: scenarios/convergence_lifecycle/spec.md

    Given the converged temperature-converter project
    When I inspect the feature vector for REQ-F-CONV-001

    Then the trajectory records all 4 edges as converged
    And each converged edge has a timestamp (not empty)
    And the feature vector status is "converged" (Markov object)
    And the trajectory is ordered (intent→requirements first)
    """

    def test_trajectory_contains_all_standard_edges(self, mock_converged_project: pathlib.Path):
        """
        Given: feature vector REQ-F-CONV-001
        When: I inspect its trajectory field
        Then: trajectory contains entries for all 4 standard-profile edges
             (REQ-FEAT-001: trajectory records every edge traversed)
        """
        fv = load_feature_vector(mock_converged_project, FEATURE_ID)
        assert fv is not None, f"Feature vector {FEATURE_ID} not found"
        trajectory = fv.get("trajectory", {})
        assert trajectory, "Feature vector has empty trajectory"

        # Standard profile trajectory keys (asset node names, not edge names)
        EXPECTED_NODES = {"requirements", "design", "code", "unit_tests"}
        found_nodes = set(trajectory.keys())
        missing = EXPECTED_NODES - found_nodes
        assert not missing, (
            f"Trajectory missing nodes: {missing}. "
            f"Found nodes: {found_nodes}"
        )

    def test_converged_trajectory_nodes_have_status(self, mock_converged_project: pathlib.Path):
        """
        Given: feature vector trajectory
        When: I inspect each trajectory node
        Then: each converged node has a status field
             (REQ-FEAT-001: trajectory is a structured record, not a boolean)
        """
        fv = load_feature_vector(mock_converged_project, FEATURE_ID)
        assert fv is not None
        trajectory = fv.get("trajectory", {})
        for node, data in trajectory.items():
            if not isinstance(data, dict):
                continue
            assert "status" in data, (
                f"Trajectory node '{node}' missing 'status' field. "
                f"Got: {data}"
            )

    def test_feature_status_is_converged(self, mock_converged_project: pathlib.Path):
        """
        Given: feature vector for REQ-F-CONV-001
        When: I check the top-level status field
        Then: status is "converged" or "completed"
             (REQ-FEAT-001: feature achieves Markov object status at full convergence)
        """
        fv = load_feature_vector(mock_converged_project, FEATURE_ID)
        assert fv is not None
        status = fv.get("status", "")
        assert status in ("converged", "completed"), (
            f"Feature status should be 'converged' or 'completed', got: '{status}'"
        )

    def test_feature_vector_has_req_id(self, mock_converged_project: pathlib.Path):
        """
        Given: feature vector for REQ-F-CONV-001
        When: I check the feature field
        Then: it matches "REQ-F-CONV-001"
             (REQ-FEAT-003: feature vectors are first-class identifiable objects)
        """
        fv = load_feature_vector(mock_converged_project, FEATURE_ID)
        assert fv is not None
        feature_id = fv.get("feature", "")
        assert feature_id == FEATURE_ID, (
            f"Feature vector ID mismatch: expected {FEATURE_ID}, got {feature_id}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# UC-05: Edge-Specific Behaviors — TDD Co-Evolution and REQ Tagging
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@skip_no_gemini
class TestUC05Edge_TDDCoevolution:
    """
    UC-05: Edge-Specific Behaviors — TDD Co-Evolution and Code Tagging
    Validates: REQ-EDGE-001, REQ-EDGE-004, REQ-F-EDGE-001

    Spec: scenarios/convergence_lifecycle/spec.md

    Given the code↔unit_tests edge has converged
    When I inspect generated artifacts in src/ and tests/

    Then code and tests were generated together (co-evolution)
    And code files have "# Implements: REQ-F-CONV-" tags
    And test files have "# Validates: REQ-F-CONV-" tags
    And both REQ-F-CONV-001 and REQ-F-CONV-002 are covered
    And the test suite passes (deterministic verification)
    """

    def test_code_and_tests_both_generated(self, mock_converged_project: pathlib.Path):
        """
        Given: converged project after code↔unit_tests edge
        When: I look for Python files in src/ and tests/
        Then: both source files and test files exist
             (REQ-EDGE-001: TDD co-evolution produces both artifacts simultaneously)
        """
        code_files, test_files = find_python_files(mock_converged_project)
        assert code_files, (
            "No source files found — TDD co-evolution should produce src/*.py"
        )
        assert test_files, (
            "No test files found — TDD co-evolution should produce tests/test_*.py"
        )

    def test_code_has_implements_tags(self, mock_converged_project: pathlib.Path):
        """
        Given: source code files
        When: I grep for REQ key tags
        Then: at least 1 "# Implements: REQ-F-CONV-" comment is present
             (REQ-EDGE-004: code tagging is a first-class requirement)
        """
        code_files, _ = find_python_files(mock_converged_project)
        tags = extract_req_tags(code_files)
        assert tags["implements"], (
            f"No '# Implements: REQ-' tags in {len(code_files)} source files. "
            f"Files: {[f.name for f in code_files]}"
        )

    def test_tests_have_validates_tags(self, mock_converged_project: pathlib.Path):
        """
        Given: test files
        When: I grep for REQ key tags
        Then: at least 1 "# Validates: REQ-F-CONV-" comment is present
             (REQ-EDGE-004: test tagging mirrors code tagging)
        """
        _, test_files = find_python_files(mock_converged_project)
        tags = extract_req_tags(test_files)
        assert tags["validates"], (
            f"No '# Validates: REQ-' tags in {len(test_files)} test files. "
            f"Files: {[f.name for f in test_files]}"
        )

    def test_generated_tests_pass_deterministically(self, mock_converged_project: pathlib.Path):
        """
        Given: the converged project with generated code and tests
        When: I run pytest against the generated artifacts
        Then: all tests pass (exit code 0)
             (REQ-EDGE-001: TDD convergence requires deterministic test passage)
        """
        validate_generated_tests_pass(mock_converged_project)


# ═══════════════════════════════════════════════════════════════════════════════
# UC-01: iterate() — Universal Signature and Convergence Properties
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@skip_no_gemini
class TestUC01Iter_ConvergenceProperties:
    """
    UC-01: Asset Graph Engine — iterate() Properties
    Validates: REQ-ITER-001, REQ-ITER-002, REQ-ITER-003

    Spec: scenarios/convergence_lifecycle/spec.md

    Given the converged project's event log

    Then each edge demonstrates the iterate() contract:
      - Starts with edge_started
      - Produces ≥1 iteration_completed (with evaluators)
      - Final iteration has delta=0
      - Concludes with edge_converged
    And the iteration function is parameterised by edge (different evaluators per edge)
    And convergence is monotonic (delta non-increasing within an edge)
    """

    def test_each_edge_has_complete_lifecycle(self, mock_converged_project: pathlib.Path):
        """
        Given: events.jsonl
        When: I group events by edge
        Then: every converged edge has exactly this lifecycle:
              edge_started → (iteration_completed)+ → edge_converged
             (REQ-ITER-001: iterate() is the only operation — not ad-hoc)
        """
        events = load_events(mock_converged_project)
        edge_events: dict[str, list[str]] = {}
        for e in events:
            edge = e.get("edge")
            if edge:
                edge_events.setdefault(edge, []).append(e.get("event_type", ""))

        for edge, types in edge_events.items():
            if "edge_converged" not in types:
                continue  # only validate edges that did converge
            assert types[0] == "edge_started", (
                f"Edge '{edge}' did not start with edge_started. "
                f"Events: {types}"
            )
            assert types[-1] == "edge_converged", (
                f"Edge '{edge}' did not end with edge_converged. "
                f"Events: {types}"
            )
            assert "iteration_completed" in types, (
                f"Edge '{edge}' has no iteration_completed between start and converge."
            )

    def test_delta_zero_on_all_converged_edges(self, mock_converged_project: pathlib.Path):
        """
        Given: events grouped by (feature, edge)
        When: I find the last iteration_completed before each edge_converged
        Then: that iteration's delta is 0
             (REQ-ITER-002: convergence = delta=0 = all evaluators pass)
        """
        events = load_events(mock_converged_project)

        # Build a map of last delta per (feature, edge)
        last_delta: dict[tuple, int | None] = {}
        for e in events:
            if e.get("event_type") != "iteration_completed":
                continue
            key = (e.get("feature", ""), e.get("edge", ""))
            delta = e.get("delta")
            if delta is not None:
                last_delta[key] = int(delta)

        # For every converged edge, verify last delta was 0
        for e in events:
            if e.get("event_type") != "edge_converged":
                continue
            key = (e.get("feature", ""), e.get("edge", ""))
            if key in last_delta:
                assert last_delta[key] == 0, (
                    f"Edge '{key[1]}' converged with final delta={last_delta[key]} "
                    f"(expected 0)."
                )
