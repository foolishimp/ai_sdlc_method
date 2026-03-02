# Implements: REQ-COORD-005, REQ-EVAL-003
from pathlib import Path
from gemini_cli.engine.state import EventStore

class EscalateCommand:
    """Explicitly escalate a feature/edge to human review."""
    
    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.store = EventStore(workspace_root)

    def run(self, feature: str, edge: str, reason: str):
        print(f"\n[ESCALATION] Escalating {feature} on {edge}...")
        print(f"Reason: {reason}")
        
        self.store.emit(
            "convergence_escalated",
            project=self.design_name.replace("_genesis", ""),
            feature=feature,
            edge=edge,
            data={
                "reason": reason,
                "severity": "critical",
                "escalated_by": "sub-agent"
            }
        )
        
        # Also raise an intent for it to appear in spec-review
        self.store.emit(
            "intent_raised",
            project=self.design_name.replace("_genesis", ""),
            data={
                "trigger": "manual_escalation",
                "signal_source": "process_gap",
                "affected_req_keys": [feature],
                "description": f"Manual escalation for {feature}: {reason}",
                "severity": "critical"
            }
        )
        
        print(f"Escalation event and intent emitted for {feature}.")
