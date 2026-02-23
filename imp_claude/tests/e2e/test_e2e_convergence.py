# Validates: REQ-TOOL-005, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
"""E2E convergence tests — headless Claude drives full methodology.

These tests scaffold a tiny Python project (temperature converter),
run headless Claude to converge it through the standard profile (4 edges),
then validate every output artifact: events, feature vectors, generated
code, and cross-artifact consistency.

The `converged_project` fixture is session-scoped — Claude runs ONCE,
all tests validate the same output.

Run:
    pytest imp_claude/tests/e2e/ -v -m e2e -s
"""

import pathlib

import pytest

from conftest import skip_no_claude
from validators import (
    extract_req_tags,
    find_python_files,
    load_events,
    load_feature_vector,
    validate_all_edges_converged,
    validate_code_traceability,
    validate_delta_decreases_to_zero,
    validate_evaluator_counts,
    validate_event_common_fields,
    validate_event_feature_consistency,
    validate_feature_vector_converged,
    validate_feature_vector_required_fields,
    validate_generated_tests_pass,
    validate_iteration_sequences,
    validate_req_key_consistency,
    validate_required_event_types,
    validate_timestamps_monotonic,
    validate_trajectory_timestamps,
    validate_requirements_populated,
)

FEATURE_ID = "REQ-F-CONV-001"
REQUIRED_REQS = {"REQ-F-CONV-001", "REQ-F-CONV-002"}


@pytest.mark.e2e
@skip_no_claude
class TestE2EConvergence:
    """Full convergence validation — 22 tests across 4 categories."""

    # ═══════════════════════════════════════════════════════════════════
    # EVENTS (9 tests)
    # ═══════════════════════════════════════════════════════════════════

    def test_events_file_exists(self, converged_project: pathlib.Path):
        """events.jsonl must exist after convergence."""
        events_file = converged_project / ".ai-workspace" / "events" / "events.jsonl"
        assert events_file.exists(), f"events.jsonl not found at {events_file}"

    def test_events_valid_json(self, converged_project: pathlib.Path):
        """Every line in events.jsonl must be valid JSON."""
        events = load_events(converged_project)
        assert len(events) > 0, "events.jsonl is empty"

    def test_events_common_fields(self, converged_project: pathlib.Path):
        """Every event must have event_type and timestamp."""
        events = load_events(converged_project)
        validate_event_common_fields(events)

    def test_events_timestamps_monotonic(self, converged_project: pathlib.Path):
        """Event timestamps must not go backward."""
        events = load_events(converged_project)
        validate_timestamps_monotonic(events)

    def test_events_required_types(self, converged_project: pathlib.Path):
        """Must contain project_initialized, edge_started, iteration_completed, edge_converged."""
        events = load_events(converged_project)
        validate_required_event_types(events)

    def test_events_iteration_sequences(self, converged_project: pathlib.Path):
        """Iteration numbers per feature+edge should be sequential."""
        events = load_events(converged_project)
        validate_iteration_sequences(events)

    def test_events_delta_to_zero(self, converged_project: pathlib.Path):
        """Final iteration delta should be 0 for converged edges."""
        events = load_events(converged_project)
        validate_delta_decreases_to_zero(events)

    def test_events_evaluator_counts(self, converged_project: pathlib.Path):
        """Iteration events should reference evaluator results."""
        events = load_events(converged_project)
        validate_evaluator_counts(events)

    def test_events_all_edges_converged(self, converged_project: pathlib.Path):
        """All 4 standard-profile edges must have edge_converged events."""
        events = load_events(converged_project)
        validate_all_edges_converged(events, FEATURE_ID)

    # ═══════════════════════════════════════════════════════════════════
    # FEATURE VECTORS (5 tests)
    # ═══════════════════════════════════════════════════════════════════

    def test_feature_vector_exists(self, converged_project: pathlib.Path):
        """Feature vector YAML must exist after convergence."""
        fv = load_feature_vector(converged_project, FEATURE_ID)
        assert fv is not None

    def test_feature_vector_converged(self, converged_project: pathlib.Path):
        """Feature vector should show converged status."""
        fv = load_feature_vector(converged_project, FEATURE_ID)
        validate_feature_vector_converged(fv)

    def test_feature_vector_required_fields(self, converged_project: pathlib.Path):
        """Feature vector must have core fields populated."""
        fv = load_feature_vector(converged_project, FEATURE_ID)
        validate_feature_vector_required_fields(fv)

    def test_feature_vector_trajectory_timestamps(self, converged_project: pathlib.Path):
        """Converged trajectory edges should have timestamps."""
        fv = load_feature_vector(converged_project, FEATURE_ID)
        validate_trajectory_timestamps(fv)

    def test_feature_vector_requirements_populated(self, converged_project: pathlib.Path):
        """Feature vector should have a valid REQ-F-* ID."""
        fv = load_feature_vector(converged_project, FEATURE_ID)
        validate_requirements_populated(fv)

    # ═══════════════════════════════════════════════════════════════════
    # GENERATED CODE (5 tests)
    # ═══════════════════════════════════════════════════════════════════

    def test_code_files_exist(self, converged_project: pathlib.Path):
        """Claude should have generated Python source files."""
        code_files, _ = find_python_files(converged_project)
        assert code_files, (
            "No Python code files found. "
            "Expected Claude to generate src/*.py or similar."
        )

    def test_test_files_exist(self, converged_project: pathlib.Path):
        """Claude should have generated Python test files."""
        _, test_files = find_python_files(converged_project)
        assert test_files, (
            "No Python test files found. "
            "Expected Claude to generate tests/test_*.py or similar."
        )

    def test_code_implements_tags(self, converged_project: pathlib.Path):
        """Generated code must have Implements: REQ-F-CONV-* tags."""
        code_files, _ = find_python_files(converged_project)
        tags = extract_req_tags(code_files)
        assert tags["implements"], (
            f"No Implements tags found in {len(code_files)} code files. "
            f"Files: {[f.name for f in code_files]}"
        )

    def test_test_validates_tags(self, converged_project: pathlib.Path):
        """Generated tests must have Validates: REQ-F-CONV-* tags."""
        _, test_files = find_python_files(converged_project)
        tags = extract_req_tags(test_files)
        assert tags["validates"], (
            f"No Validates tags found in {len(test_files)} test files. "
            f"Files: {[f.name for f in test_files]}"
        )

    def test_generated_tests_pass(self, converged_project: pathlib.Path):
        """Generated tests should pass when run with pytest."""
        validate_generated_tests_pass(converged_project)

    # ═══════════════════════════════════════════════════════════════════
    # CONSISTENCY (3 tests)
    # ═══════════════════════════════════════════════════════════════════

    def test_code_traceability(self, converged_project: pathlib.Path):
        """REQ keys must appear in both code Implements and test Validates tags."""
        validate_code_traceability(converged_project, REQUIRED_REQS)

    def test_req_key_consistency(self, converged_project: pathlib.Path):
        """Feature vector REQs should appear in generated code/test tags."""
        validate_req_key_consistency(converged_project, REQUIRED_REQS)

    def test_event_feature_consistency(self, converged_project: pathlib.Path):
        """Event log feature references should match actual feature vectors."""
        events = load_events(converged_project)
        validate_event_feature_consistency(events, {FEATURE_ID})
