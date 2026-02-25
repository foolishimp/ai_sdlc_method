# Validates: REQ-SUPV-001, REQ-SUPV-002
import pytest
from gemini_cli.internal.workspace_state import classify_tolerance_breach, get_unactioned_escalations

pytestmark = [pytest.mark.uat]

class TestIntentEngineInterface:
    def test_three_ambiguity_regimes(self, affect_triage):
        rules = affect_triage.get("classification_rules", [])
        assert len(rules) > 0
        escalation_types = {r.get("escalation") for r in rules}
        assert "always" in escalation_types
        assert "threshold" in escalation_types
        assert "agent_decides" in escalation_types

    def test_classify_tolerance_breach(self):
        assert classify_tolerance_breach(5, 10) == "reflex.log"
        assert classify_tolerance_breach(15, 10) == "specEventLog"
        assert classify_tolerance_breach(25, 10) == "escalate"
        assert classify_tolerance_breach(11, 10, severity="critical") == "escalate"

class TestConstraintTolerances:
    def test_constraints_have_thresholds(self, sensory_monitors):
        for monitor_type in ("interoceptive", "exteroceptive"):
            monitors = sensory_monitors.get("monitors", {}).get(monitor_type, [])
            for m in monitors:
                if not m.get("enabled", True):
                    continue
                has_criteria = (
                    m.get("threshold") or m.get("checks") or m.get("severity_filter")
                    or m.get("commands") or m.get("sources") or m.get("endpoint")
                )
                assert has_criteria, f"Monitor {m['id']} has no criteria"

    def test_tolerance_pressure_equilibrium(self):
        from imp_gemini.tests.uat.conftest import make_event
        events = [
            make_event("intent_raised", intent_id="ESC-001"),
            make_event("spawn_created", intent_id="ESC-001"),
            make_event("intent_raised", intent_id="ESC-002"),
        ]
        unactioned = get_unactioned_escalations(events)
        assert len(unactioned) == 1
        assert unactioned[0]["intent_id"] == "ESC-002"
