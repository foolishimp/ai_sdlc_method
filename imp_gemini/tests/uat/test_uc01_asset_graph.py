# Validates: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-001, REQ-ITER-002
import pytest
from genesis_core.internal.workspace_state import load_events, detect_stuck_features

pytestmark = [pytest.mark.uat]

class TestAssetTypeRegistry:
    def test_ten_asset_types(self, graph_topology):
        types = graph_topology.get("asset_types", {})
        assert len(types) == 10
        expected = {
            "intent", "requirements", "design", "code", "unit_tests",
            "test_cases", "uat_tests", "cicd", "running_system", "telemetry",
        }
        assert set(types.keys()) == expected

    def test_asset_types_have_schema(self, graph_topology):
        for name, defn in graph_topology.get("asset_types", {}).items():
            assert "schema" in defn

class TestAdmissibleTransitions:
    def test_ten_transitions(self, graph_topology):
        transitions = graph_topology.get("transitions", [])
        assert len(transitions) == 10

class TestIterateFunction:
    def test_universal_signature(self):
        # In Gemini CLI, the iterate agent is a markdown spec
        # we check if it exists and mentions the signature
        import pathlib
        project_root = pathlib.Path(__file__).parents[3]
        iterate_spec = project_root / "imp_gemini" / "gemini_cli" / "agents" / "gen-iterate.md"
        assert iterate_spec.exists()
        spec_text = iterate_spec.read_text()
        assert "Current asset" in spec_text
        assert "Context[]" in spec_text
        assert "Edge parameterisation" in spec_text

class TestConvergence:
    def test_stuck_detected(self, in_progress_workspace):
        # Add stuck events manually to in_progress_workspace
        events_file = in_progress_workspace / ".ai-workspace" / "events" / "events.jsonl"
        import json
        stuck_events = [
            {"event_type": "iteration_completed", "feature": "REQ-F-STUCK", "edge": "design→code", "delta": 5, "timestamp": "2026-02-23T12:00:00Z"},
            {"event_type": "iteration_completed", "feature": "REQ-F-STUCK", "edge": "design→code", "delta": 5, "timestamp": "2026-02-23T12:01:00Z"},
            {"event_type": "iteration_completed", "feature": "REQ-F-STUCK", "edge": "design→code", "delta": 5, "timestamp": "2026-02-23T12:02:00Z"},
        ]
        with open(events_file, "a") as f:
            for e in stuck_events:
                f.write(json.dumps(e) + "\n")
        
        stuck = detect_stuck_features(in_progress_workspace / ".ai-workspace", threshold=3)
        assert any(s["feature"] == "REQ-F-STUCK" for s in stuck)
