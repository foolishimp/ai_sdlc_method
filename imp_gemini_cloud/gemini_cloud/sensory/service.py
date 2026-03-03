from typing import List, Dict, Any, Optional
from pathlib import Path
from gemini_cloud.internal.yaml_loader import load_yaml
from gemini_cloud.engine.state import CloudEventStore

class SensoryService:
    """Simulates the GCP-native Sensory Service (Cloud Functions + Eventarc)."""
    def __init__(self, store: CloudEventStore, config_root: Path = None):
        self.store = store
        self.config_root = config_root or Path(__file__).parent.parent / "config"
        self.monitors_config = load_yaml(self.config_root / "sensory_monitors.yml")
        self.triage_config = load_yaml(self.config_root / "affect_triage.yml")

    def sense(self) -> List[Dict]:
        """Runs the monitors and collects signals."""
        signals = []
        monitors_dict = self.config_root.joinpath("sensory_monitors.yml").exists() and self.monitors_config.get("monitors", {})
        
        all_monitors = []
        if isinstance(monitors_dict, dict):
            all_monitors.extend(monitors_dict.get("interoceptive", []))
            all_monitors.extend(monitors_dict.get("exteroceptive", []))
        
        for m in all_monitors:
            # Simulate running a monitor
            signal = {
                "source": m.get("name"),
                "type": "interoceptive" if m in monitors_dict.get("interoceptive", []) else "exteroceptive",
                "severity": "info",
                "message": f"Monitor {m.get('name')} checked."
            }
            signals.append(signal)
            self.store.emit("sensory_signal_received", data=signal)
            
        return signals

    def triage(self, signals: List[Dict]) -> List[Dict]:
        """Triages signals into intents or proposals using Vertex AI."""
        proposals = []
        for s in signals:
            # Simulate Vertex AI triage
            # ADR-GC-015: Vertex AI classifies ambiguity and severity
            is_serious = s.get("severity") in ["high", "critical"]
            if is_serious:
                proposal = {
                    "event_type": "intent_raised",
                    "feature": "SYSTEM",
                    "data": {
                        "description": f"Auto-generated intent from signal: {s.get('message')}",
                        "source": "sensory_service",
                        "priority": s.get("severity")
                    }
                }
                proposals.append(proposal)
                self.store.emit("intent_raised", feature="SYSTEM", data=proposal["data"])
        
        return proposals
