# Implements: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-SENSE-006, REQ-F-SENSE-001
import os
import json
import yaml
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from gemini_cli.engine.state import EventStore
from gemini_cli.engine.otlp_relay import OTLPRelay

class SensoryService:
    """Independent service that watches the workspace and runs monitors.
    Implements: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.project_root = workspace_root.parent
        self.store = EventStore(workspace_root)
        self.config_path = Path(__file__).parent.parent / "config" / "sensory_monitors.yml"
        self.config = self._load_config()
        self.running = False
        self._last_mtimes = {} 
        self.pid_file = workspace_root / "SENSORY_PID"
        
        # OTLP Projection (ADR-S-014)
        endpoint = os.environ.get("OTLP_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
        self.relay = OTLPRelay(workspace_root, collector_endpoint=endpoint)

    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    def is_service_running(self) -> bool:
        """Check if the background process is alive via PID file."""
        if not self.pid_file.exists():
            return False
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, 0) # Throws ProcessLookupError if not running
            return True
        except (OSError, ValueError):
            return False

    def run_continuous_loop(self, interval: int = 60):
        """The main execution loop for the background process."""
        # Write PID
        self.pid_file.write_text(str(os.getpid()))
        self.running = True
        
        # Start the OTLP Relay (ADR-S-014)
        self.relay.start()
        
        try:
            while self.running:
                try:
                    self.run_all_monitors()
                except Exception as e:
                    # Log error to event stream
                    self.store.emit("interoceptive_signal", project="imp_gemini", data={"severity": "error", "message": f"Sensory loop error: {e}"})
                time.sleep(interval)
        finally:
            if self.pid_file.exists():
                self.pid_file.unlink()

    def start_background_service(self, interval: int = 60):
        """Triggers the background process via shell (ADR-GG-005)."""
        if self.is_service_running():
            print("  [SENSE] Sensory service is already running.")
            return

        # Use the relative path to the entry point
        cmd = f"python3 -m gemini_cli.engine.sensory_loop --workspace {self.workspace_root} --interval {interval}"
        print(f"  [SENSE] Launching background sensory process ({interval}s interval)...")
        subprocess.Popen(cmd.split(), cwd=self.project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop(self):
        """Stops the background process."""
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                os.kill(pid, 15) # SIGTERM
                print(f"  [SENSE] Stopped sensory service (PID: {pid})")
            except OSError:
                pass
            self.pid_file.unlink()
        self.running = False
        self.relay.stop()

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
        
        # 3. Artifact Write Observation (REQ-SENSE-005)
        self._check_artifact_writes()

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
                for cmd_type, cmd in commands.items():
                    if "python" in cmd_type or "pip" in cmd:
                        try:
                            # Use timeout to prevent hanging the service
                            res = subprocess.check_output(cmd, shell=True, text=True, timeout=10)
                            self._emit_signal(event_type, monitor_id, name, {"output": res})
                            break
                        except:
                            continue
        except Exception as e:
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

    def _check_artifact_writes(self):
        """Detects new or modified artifacts (REQ-SENSE-005)."""
        # If this is the very first time we check, we just establish a baseline
        is_initializing = getattr(self, "_sensory_initialized", False) == False
        
        # Scan core directories
        for folder in ["specification", "design", "code", "tests", "comments"]:
            path = self.project_root / folder
            if not path.exists():
                # Check inside .ai-workspace too
                path = self.workspace_root / folder
                if not path.exists(): continue
            
            for file in path.rglob("*"):
                if file.is_file() and file.suffix in [".md", ".py", ".yml"]:
                    mtime = file.stat().st_mtime
                    file_str = str(file.relative_to(self.project_root))
                    
                    if file_str in self._last_mtimes:
                        if mtime > self._last_mtimes[file_str]:
                            self._emit_signal(
                                "exteroceptive_signal", 
                                "EXTRO-WRITE-001", 
                                "artifact_write", 
                                {"file": file_str, "status": "modified", "severity": "info"}
                            )
                    elif not is_initializing:
                        # New file detected after baseline established
                        self._emit_signal(
                            "exteroceptive_signal", 
                            "EXTRO-WRITE-001", 
                            "artifact_write", 
                            {"file": file_str, "status": "new", "severity": "info"}
                        )
                    
                    self._last_mtimes[file_str] = mtime
        
        self._sensory_initialized = True

    # --- Concrete Monitor Implementations ---

    def _monitor_event_freshness(self, monitor: Dict) -> Optional[Dict]:
        events = self.store.load_all()
        if not events:
            return {"days_since_last_event": 999, "severity": "warning"}
        
        last_event = events[-1]
        ts_str = last_event.get("timestamp") or last_event.get("eventTime")
        if not ts_str: return None
        
        last_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - last_ts
        days = delta.total_seconds() / (24 * 3600)
        
        threshold = monitor.get("threshold", {})
        if days >= threshold.get("warning", 7):
            return {"days_since_last_event": round(days, 2), "status": "stale", "severity": "warning"}
        return None

    def _monitor_feature_vector_stall(self, monitor: Dict) -> Optional[Dict]:
        """INTRO-002: In-progress vectors with no activity."""
        features_dir = self.workspace_root / "features" / "active"
        if not features_dir.exists(): return None
        
        stalled = []
        now = datetime.now(timezone.utc)
        threshold = monitor.get("threshold", {}).get("warning", 14)
        
        for path in features_dir.glob("*.yml"):
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                if data and data.get("status") != "converged":
                    # Check mtime of the file as proxy for last activity
                    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                    days = (now - mtime).days
                    if days >= threshold:
                        stalled.append({"feature": data.get("feature"), "days": days})
        
        if stalled:
            return {"stalled_features": stalled, "severity": "warning"}
        return None

    def _monitor_status_freshness(self, monitor: Dict) -> Optional[Dict]:
        status_file = self.workspace_root / "STATUS.md"
        if not status_file.exists():
            return {"status": "missing", "severity": "warning"}
        
        mtime = datetime.fromtimestamp(status_file.stat().st_mtime, tz=timezone.utc)
        events = self.store.load_all()
        if not events:
            return None
            
        ts_str = events[-1].get("timestamp") or events[-1].get("eventTime")
        if not ts_str: return None
        
        last_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if last_ts > mtime:
            lag = (last_ts - mtime).total_seconds() / (24 * 3600)
            threshold = monitor.get("threshold", {})
            if lag >= threshold.get("warning", 1):
                return {"status_lag_days": round(lag, 2), "severity": "info"}
        return None
