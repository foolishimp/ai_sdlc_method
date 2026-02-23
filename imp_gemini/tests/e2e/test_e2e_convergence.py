# Validates: REQ-TOOL-005, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
import pathlib
import pytest
from imp_gemini.tests.e2e.conftest import skip_no_gemini
from imp_gemini.tests.e2e.validators import (
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
REQUIRED_REQS = {"REQ-F-CONV-001"}

@pytest.mark.e2e
@skip_no_gemini
class TestE2EConvergence:
    """REAL E2E validation — full agentic loop."""

    def test_events_file_exists(self, real_converged_project: pathlib.Path):
        events_file = real_converged_project / ".ai-workspace" / "events" / "events.jsonl"
        assert events_file.exists()

    def test_events_valid_json(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        assert len(events) > 0

    def test_events_common_fields(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        validate_event_common_fields(events)

    def test_events_timestamps_monotonic(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        validate_timestamps_monotonic(events)

    def test_events_required_types(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        validate_required_event_types(events)

    def test_events_iteration_sequences(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        validate_iteration_sequences(events)

    def test_events_delta_to_zero(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        validate_delta_decreases_to_zero(events)

    def test_events_all_edges_converged(self, real_converged_project: pathlib.Path):
        events = load_events(real_converged_project)
        validate_all_edges_converged(events, FEATURE_ID)

    def test_feature_vector_exists(self, real_converged_project: pathlib.Path):
        fv = load_feature_vector(real_converged_project, FEATURE_ID)
        assert fv is not None

    def test_feature_vector_converged(self, real_converged_project: pathlib.Path):
        fv = load_feature_vector(real_converged_project, FEATURE_ID)
        validate_feature_vector_converged(fv)

    def test_code_files_exist(self, real_converged_project: pathlib.Path):
        code_files, _ = find_python_files(real_converged_project)
        assert code_files

    def test_test_files_exist(self, real_converged_project: pathlib.Path):
        _, test_files = find_python_files(real_converged_project)
        assert test_files

    def test_generated_tests_pass(self, real_converged_project: pathlib.Path):
        validate_generated_tests_pass(real_converged_project)

    def test_code_traceability(self, real_converged_project: pathlib.Path):
        validate_code_traceability(real_converged_project, REQUIRED_REQS)
