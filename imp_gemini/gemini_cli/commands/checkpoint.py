# Implements: REQ-TOOL-008
import shutil
from pathlib import Path
from datetime import datetime, timezone
from gemini_cli.engine.state import EventStore

class CheckpointCommand:
    """Saves a snapshot of the current workspace state."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)

    def run(self, label: str = None):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        name = f"checkpoint_{label}_{ts}" if label else f"checkpoint_{ts}"
        
        snapshot_dir = self.workspace_root / "snapshots" / name
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Snapshot features and events
        for sub in ["features", "events"]:
            src = self.workspace_root / sub
            if src.exists():
                shutil.copytree(src, snapshot_dir / sub, dirs_exist_ok=True)
        
        self.store.emit(
            event_type="checkpoint_created",
            project="imp_gemini",
            data={"name": name, "label": label}
        )
        
        print(f"  [CHECKPOINT] Workspace snapshotted to {snapshot_dir}")
        return True
