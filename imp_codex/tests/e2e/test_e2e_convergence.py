# Validates: REQ-TOOL-005, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
"""Codex Genesis end-to-end convergence validation."""

from __future__ import annotations

import pathlib

import pytest

from .validators import (
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
    validate_requirements_populated,
    validate_timestamps_monotonic,
    validate_trajectory_timestamps,
)

FEATURE_ID = "REQ-F-CONV-001"
REQUIRED_REQS = {"REQ-F-CONV-001", "REQ-F-CONV-002"}


@pytest.mark.e2e
class TestE2EConvergence:
    """End-to-end validation for one full standard-profile convergence."""

    # Events
    def test_events_file_exists(self, converged_project: pathlib.Path):
        events_file = converged_project / ".ai-workspace" / "events" / "events.jsonl"
        assert events_file.exists()

    def test_events_valid_json(self, converged_project: pathlib.Path):
        events = load_events(converged_project)
        assert len(events) > 0

    def test_events_common_fields(self, converged_project: pathlib.Path):
        validate_event_common_fields(load_events(converged_project))

    def test_events_timestamps_monotonic(self, converged_project: pathlib.Path):
        validate_timestamps_monotonic(load_events(converged_project))

    def test_events_required_types(self, converged_project: pathlib.Path):
        validate_required_event_types(load_events(converged_project))

    def test_events_iteration_sequences(self, converged_project: pathlib.Path):
        validate_iteration_sequences(load_events(converged_project))

    def test_events_delta_to_zero(self, converged_project: pathlib.Path):
        validate_delta_decreases_to_zero(load_events(converged_project))

    def test_events_evaluator_counts(self, converged_project: pathlib.Path):
        validate_evaluator_counts(load_events(converged_project))

    def test_events_all_edges_converged(self, converged_project: pathlib.Path):
        validate_all_edges_converged(load_events(converged_project), FEATURE_ID)

    # Feature vector
    def test_feature_vector_exists(self, converged_project: pathlib.Path):
        assert load_feature_vector(converged_project, FEATURE_ID)

    def test_feature_vector_converged(self, converged_project: pathlib.Path):
        validate_feature_vector_converged(load_feature_vector(converged_project, FEATURE_ID))

    def test_feature_vector_required_fields(self, converged_project: pathlib.Path):
        validate_feature_vector_required_fields(load_feature_vector(converged_project, FEATURE_ID))

    def test_feature_vector_trajectory_timestamps(self, converged_project: pathlib.Path):
        validate_trajectory_timestamps(load_feature_vector(converged_project, FEATURE_ID))

    def test_feature_vector_requirements_populated(self, converged_project: pathlib.Path):
        validate_requirements_populated(load_feature_vector(converged_project, FEATURE_ID))

    # Generated code/tests
    def test_code_files_exist(self, converged_project: pathlib.Path):
        code_files, _ = find_python_files(converged_project)
        assert code_files

    def test_test_files_exist(self, converged_project: pathlib.Path):
        _, test_files = find_python_files(converged_project)
        assert test_files

    def test_code_implements_tags(self, converged_project: pathlib.Path):
        code_files, _ = find_python_files(converged_project)
        tags = extract_req_tags(code_files)
        assert tags["implements"]

    def test_test_validates_tags(self, converged_project: pathlib.Path):
        _, test_files = find_python_files(converged_project)
        tags = extract_req_tags(test_files)
        assert tags["validates"]

    def test_generated_tests_pass(self, converged_project: pathlib.Path):
        validate_generated_tests_pass(converged_project)

    # Cross-artifact consistency
    def test_code_traceability(self, converged_project: pathlib.Path):
        validate_code_traceability(converged_project, REQUIRED_REQS)

    def test_req_key_consistency(self, converged_project: pathlib.Path):
        validate_req_key_consistency(converged_project, REQUIRED_REQS)

    def test_event_feature_consistency(self, converged_project: pathlib.Path):
        validate_event_feature_consistency(load_events(converged_project), {FEATURE_ID})

