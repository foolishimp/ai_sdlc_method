
import shutil
from pathlib import Path
from datetime import datetime, timezone
from gemini_cli.engine.state import EventStore

class CheckpointCommand:
    """Saves an immutable snapshot of the methodology state."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)

    def run(self, message: str = "Manual Checkpoint"):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        snapshot_dir = self.workspace_root / "snapshots" / f"snapshot_{timestamp}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Snapshot Features
        features_src = self.workspace_root / "features"
        if features_src.exists():
            shutil.copytree(features_src, snapshot_dir / "features", dirs_exist_ok=True)
            
        # 2. Snapshot Event Log
        events_src = self.workspace_root / "events" / "events.jsonl"
        if events_src.exists():
            shutil.copy2(events_src, snapshot_dir / "events.jsonl")
            
        # 3. Emit Checkpoint Event
        self.store.emit(
            "checkpoint_created",
            project="unknown",
            data={
                "snapshot_id": f"snapshot_{timestamp}",
                "message": message
            }
        )
        
        print(f"Checkpoint created: {snapshot_dir.name}")
