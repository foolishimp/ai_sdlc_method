# Validates: REQ-LIFE-001, ADR-S-020
"""E2E tests for v3.0 features: Hamiltonian tracking and Recursive Spawn."""

import importlib.util
import pathlib
import pytest
import yaml

# \u2500\u2500 E2E sibling-module imports \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _load_sibling(name: str):
    path = pathlib.Path(__file__).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"e2e_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_conftest = _load_sibling("conftest")
MockGeminiRunner = _conftest.MockGeminiRunner

_v = _load_sibling("validators")
load_events = _v.load_events
load_feature_vector = _v.load_feature_vector

@pytest.fixture(scope="session")
def stuck_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    """Fixture that simulates a stuck project triggering a spawn."""
    runner = MockGeminiRunner(e2e_project_dir)
    runner.run_stuck("REQ-F-CONV-001", "code\u2194unit_tests")
    return e2e_project_dir

@pytest.mark.e2e
class TestE2EV3Features:
    """Validation for Hamiltonian metrics and recursive spawning."""

    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
    # HAMILTONIAN METRICS
    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

    def test_events_carry_hamiltonian_metrics(self, mock_converged_project: pathlib.Path):
        """v3.0 events must carry hamiltonian_T and hamiltonian_V."""
        events = load_events(mock_converged_project)
        iter_events = [e for e in events if e.get("event_type") == "iteration_completed"]
        assert len(iter_events) > 0
        
        for ev in iter_events:
            assert "hamiltonian_T" in ev, f"Event {ev.get('runId')} missing hamiltonian_T"
            assert "hamiltonian_V" in ev, f"Event {ev.get('runId')} missing hamiltonian_V"

    def test_feature_vector_carries_hamiltonian_metrics(self, mock_converged_project: pathlib.Path):
        """Feature vector trajectory must store Hamiltonian metrics."""
        fv = load_feature_vector(mock_converged_project, "REQ-F-CONV-001")
        trajectory = fv.get("trajectory", {})
        
        for edge, data in trajectory.items():
            if isinstance(data, dict):
                assert "hamiltonian_T" in data, f"Edge {edge} missing hamiltonian_T"
                assert "hamiltonian_V" in data, f"Edge {edge} missing hamiltonian_V"

    def test_cumulative_t_progression(self, mock_converged_project: pathlib.Path):
        """Hamiltonian T should be cumulative across edges."""
        fv = load_feature_vector(mock_converged_project, "REQ-F-CONV-001")
        trajectory = fv.get("trajectory", {})
        
        # Sort by T to verify progression
        edge_order = ["requirements", "design", "code", "unit_tests"]
        t_values = []
        for edge in edge_order:
            data = trajectory.get(edge)
            if isinstance(data, dict):
                t_values.append(data.get("hamiltonian_T", 0))
        
        assert len(t_values) >= 4
        assert sorted(t_values) == t_values, f"Hamiltonian T should be non-decreasing: {t_values}"
        assert len(set(t_values)) == len(t_values), f"Hamiltonian T should be unique per edge: {t_values}"

    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
    # RECURSIVE SPAWN
    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

    def test_stuck_delta_triggers_spawn_event(self, stuck_project: pathlib.Path):
        """3 iterations with same delta triggers a spawn_created event."""
        events = load_events(stuck_project)
        spawn_events = [e for e in events if e.get("event_type") == "spawn_created"]
        assert len(spawn_events) == 1
        
        ev = spawn_events[0]
        assert ev["feature"] == "REQ-F-CONV-001"
        assert ev["child_feature"] == "REQ-F-DISCOVERY-001"
        assert ev["payload"]["triggered_at_edge"] == "code\u2194unit_tests"

    def test_parent_vector_blocked_by_child(self, stuck_project: pathlib.Path):
        """Parent feature vector must be 'blocked' and reference the child."""
        fv = load_feature_vector(stuck_project, "REQ-F-CONV-001")
        trajectory = fv.get("trajectory", {})
        
        # The key in trajectory might be unit_tests (target) or code_unit_tests (normalized)
        edge_data = trajectory.get("unit_tests") or trajectory.get("code_unit_tests")
        assert edge_data is not None
        assert edge_data["status"] == "blocked"
        assert edge_data["blocked_by"] == "REQ-F-DISCOVERY-001"

    def test_spawn_created_carries_context_hints(self, stuck_project: pathlib.Path):
        """Spawn event should carry the question or context hints."""
        events = load_events(stuck_project)
        spawn_ev = next(e for e in events if e.get("event_type") == "spawn_created")
        payload = spawn_ev.get("payload", {})
        assert "question" in payload
        assert "Stuck" in payload["question"]
