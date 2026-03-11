# Implements: REQ-SENSE-004, ADR-S-027
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from gemini_cli.engine.state import EventStore

class AffectTriageEngine:
    """Classifies sensory signals and raises intents with spec-change branching.
    Implements: REQ-SENSE-004, ADR-S-027
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)
        self.config_path = Path(__file__).parent.parent / "config" / "affect_triage.yml"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    def _triage_signal(self, signal: Dict):
        data = signal.get("data", {})
        monitor_id = data.get("monitor_id")
        valence = data.get("valence", {})
        severity = valence.get("severity", "info")
        
        # 1. Check for specific comment signal (REQ-LIFE-006)
        if data.get("name") == "artifact_write" and "comments/" in data.get("file", ""):
            self._raise_intent(signal, {
                "gap_type": "missing_consensus",
                "description": f"New stakeholder comment detected: {data.get('file')}"
            })
            return

        # 2. Rule-based triage
        rules = self.config.get("rules", [])
        for rule in rules:
            if rule.get("monitor_id") == monitor_id and rule.get("severity") == severity:
                action = rule.get("action")
                if action == "raise_intent":
                    self._raise_intent(signal, rule)

    def _raise_intent(self, signal: Dict, rule: Dict):
        """Raises an intent with the ADR-S-027 spec-change branch."""
        data = signal.get("data", {})
        gap_type = data.get("gap_type", "unknown")
        
        # ADR-S-026.1 Classification Table
        spec_change_map = {
            "missing_requirements": True,
            "unknown_domain": True,
            "spec_drift": True,
            "missing_consensus": True,
            "missing_schema": False,
            "missing_design": False,
            "unknown_risk": False,
            "missing_telemetry": False
        }
        
        requires_spec_change = spec_change_map.get(gap_type, True) # Default to True for safety
        
        self.store.emit(
            "intent_raised",
            project=signal.get("project", "unknown"),
            data={
                "trigger": "sensory_signal",
                "signal_id": signal.get("timestamp"),
                "gap_type": gap_type,
                "requires_spec_change": requires_spec_change,
                "description": rule.get("description", f"Intent raised due to {data.get('name')} signal.")
            }
        )
