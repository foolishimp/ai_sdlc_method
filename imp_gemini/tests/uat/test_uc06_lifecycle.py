# Validates: REQ-LIFE-001, REQ-LIFE-002, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-008
import pytest
from imp_gemini.code.internal.workspace_state import load_events

pytestmark = [pytest.mark.uat]

class TestCICDEdge:
    def test_cicd_transitions_exist(self, graph_topology):
        transitions = graph_topology.get("transitions", [])
        code_cicd = [t for t in transitions if t["source"] == "code" and t["target"] == "cicd"]
        assert len(code_cicd) == 1
        assert code_cicd[0]["evaluators"] == ["deterministic"]

class TestTelemetryHomeostasis:
    def test_telemetry_tagged_with_req(self, graph_topology):
        asset_types = graph_topology.get("asset_types", {})
        telemetry = asset_types.get("telemetry", {})
        assert "req_tags" in telemetry.get("schema", {})

class TestIntentEvents:
    def test_intent_raised_event(self, in_progress_workspace):
        ws = in_progress_workspace / ".ai-workspace"
        from imp_gemini.tests.uat.conftest import make_event, write_events
        intent_event = make_event(
            "intent_raised",
            data={
                "intent_id": "INT-DEV-001",
                "signal_source": "test_failure",
                "affected_req_keys": ["REQ-F-BETA-001"],
            }
        )
        events = load_events(ws)
        events.append(intent_event)
        write_events(ws / "events" / "events.jsonl", events)
        
        all_events = load_events(ws)
        intents = [e for e in all_events if e["event_type"] == "intent_raised"]
        assert len(intents) == 1
        assert intents[0]["data"]["intent_id"] == "INT-DEV-001"

class TestSignalClassification:
    def test_signal_types_defined(self, affect_triage):
        rules = affect_triage.get("classification_rules", [])
        assert len(rules) >= 5

class TestProtocolEnforcement:
    def test_hooks_exist(self):
        import pathlib
        hooks_file = pathlib.Path("/Users/jim/src/apps/ai_sdlc_method/imp_gemini/code/hooks/hooks.json")
        assert hooks_file.exists()
