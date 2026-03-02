# Implements: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-004
import os
import json
import yaml
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from gemini_cli.engine.state import EventStore

class SensoryService:
    """Independent service that watches the workspace and runs monitors.
    Implements: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-004
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.project_root = workspace_root.parent
        self.store = EventStore(workspace_root)
        self.config_path = Path(__file__).parent.parent / "config" / "sensory_monitors.yml"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    def run_all_monitors(self):
        """Runs all enabled monitors and emits signals."""
        monitors = self.config.get("monitors", {})
        
        # 1. Interoceptive Monitors
        for monitor in monitors.get("interoceptive", []):
            if monitor.get("enabled", True):
                self._run_monitor(monitor, "interoceptive_signal")
                
        # 2. Exteroceptive Monitors
        for monitor in monitors.get("exteroceptive", []):
            if monitor.get("enabled", True):
                self._run_monitor(monitor, "exteroceptive_signal")

    def _run_monitor(self, monitor: Dict, event_type: str):
        monitor_id = monitor.get("id")
        name = monitor.get("name")
        
        try:
            # Dispatch to specific monitor logic
            method_name = f"_monitor_{name.replace('-', '_')}"
            if hasattr(self, method_name):
                result = getattr(self, method_name)(monitor)
                if result:
                    self._emit_signal(event_type, monitor_id, name, result)
            else:
                # Generic command-based monitor (mostly for exteroceptive)
                commands = monitor.get("commands", {})
                # For now, just try to run the first one that matches our environment
                # In a real implementation, we'd check the project type
                for cmd_type, cmd in commands.items():
                    # Simplified check: just try to run it if it looks like it's for our ecosystem
                    if "python" in cmd_type or "pip" in cmd:
                        try:
                            res = subprocess.check_output(cmd, shell=True, text=True)
                            self._emit_signal(event_type, monitor_id, name, {"output": res})
                            break
                        except:
                            continue
        except Exception as e:
            # Meta-monitoring: sense that sensing failed
            self.store.emit(
                "interoceptive_signal",
                project="imp_gemini",
                data={
                    "monitor_id": "META-001",
                    "severity": "warning",
                    "description": f"Monitor {monitor_id} ({name}) failed to execute: {str(e)}"
                }
            )

    def _emit_signal(self, event_type: str, monitor_id: str, name: str, data: Dict):
        # ADR-S-008: Every signal carries a Valence Vector (severity, urgency, priority)
        valence = {
            "severity": data.get("severity", "info"),
            "urgency": data.get("urgency", "low"),
            "priority": data.get("priority", "low")
        }
        
        self.store.emit(
            event_type,
            project="imp_gemini",
            data={
                "monitor_id": monitor_id,
                "name": name,
                "valence": valence,
                **data
            }
        )

    # --- Concrete Monitor Implementations ---

    def _monitor_event_freshness(self, monitor: Dict) -> Optional[Dict]:
        events = self.store.load_all()
        if not events:
            return {"days_since_last_event": 999}
        
        last_event = events[-1]
        last_ts = datetime.fromisoformat(last_event["timestamp"].replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - last_ts
        days = delta.total_seconds() / (24 * 3600)
        
        threshold = monitor.get("threshold", {})
        if days >= threshold.get("warning", 7):
            return {"days_since_last_event": round(days, 2), "status": "stale"}
        return None

    def _monitor_status_freshness(self, monitor: Dict) -> Optional[Dict]:
        status_file = self.workspace_root / "STATUS.md"
        if not status_file.exists():
            return {"status": "missing"}
        
        mtime = datetime.fromtimestamp(status_file.stat().st_mtime, tz=timezone.utc)
        events = self.store.load_all()
        if not events:
            return None
            
        last_ts = datetime.fromisoformat(events[-1]["timestamp"].replace("Z", "+00:00"))
        if last_ts > mtime:
            lag = (last_ts - mtime).total_seconds() / (24 * 3600)
            threshold = monitor.get("threshold", {})
            if lag >= threshold.get("warning", 1):
                return {"status_lag_days": round(lag, 2)}
        return None

    def _monitor_spec_code_drift(self, monitor: Dict) -> Optional[Dict]:
        # Reuse GapsCommand logic? Or implement a light version.
        # For now, just check if any gaps exist.
        from gemini_cli.commands.gaps import GapsCommand
        # This is a bit heavy, maybe just a quick scan
        return None
