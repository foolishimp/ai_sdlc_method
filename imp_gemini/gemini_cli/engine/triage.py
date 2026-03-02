# Implements: REQ-SENSE-004
import yaml
from pathlib import Path
from typing import Dict, List, Any
from gemini_cli.engine.state import EventStore

class AffectTriageEngine:
    """Classifies sensory signals and raises intents.
    Implements: REQ-SENSE-004
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

    def process_signals(self):
        """Processes recent sensory signals and performs triage."""
        events = self.store.load_all()
        # Find signals since last triage (simplified: just look at last 100 events)
        signals = [e for e in events[-100:] if e["event_type"] in ["interoceptive_signal", "exteroceptive_signal"]]
        
        for signal in signals:
            self._triage_signal(signal)

    def _triage_signal(self, signal: Dict):
        data = signal.get("data", {})
        monitor_id = data.get("monitor_id")
        valence = data.get("valence", {})
        severity = valence.get("severity", "info")
        
        # Check triage rules
        rules = self.config.get("rules", [])
        for rule in rules:
            if rule.get("monitor_id") == monitor_id and rule.get("severity") == severity:
                action = rule.get("action")
                if action == "raise_intent":
                    self._raise_intent(signal, rule)
                elif action == "propose_feature":
                    self._propose_feature(signal, rule)
                elif action == "emit_affect":
                    self._emit_affect(signal, rule)

    def _propose_feature(self, signal: Dict, rule: Dict):
        data = signal.get("data", {})
        # Simple heuristic for IDs
        proposal_id = f"PROP-{int(datetime.now().timestamp())}"
        self.store.emit(
            "feature_proposal",
            project=signal.get("project", "unknown"),
            data={
                "proposal_id": proposal_id,
                "feature_id": rule.get("proposed_fid", "REQ-F-AUTO"),
                "title": rule.get("proposed_title", "Automatic Corrective Feature"),
                "requirements": rule.get("requirements", []),
                "intent_id": data.get("monitor_id", "INT-AUTO"),
                "trigger_signal_id": signal.get("timestamp")
            }
        )

    def _raise_intent(self, signal: Dict, rule: Dict):
        data = signal.get("data", {})
        self.store.emit(
            "intent_raised",
            project=signal.get("project", "unknown"),
            data={
                "trigger": "sensory_signal",
                "signal_id": signal.get("timestamp"),
                "monitor_id": data.get("monitor_id"),
                "description": rule.get("description", f"Intent raised due to {data.get('name')} signal.")
            }
        )

    def _emit_affect(self, signal: Dict, rule: Dict):
        self.store.emit(
            "affect_triage",
            project=signal.get("project", "unknown"),
            data={
                "signal_id": signal.get("timestamp"),
                "classification": rule.get("classification", "warning"),
                "message": rule.get("description", "Affect signal emitted.")
            }
        )
