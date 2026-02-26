import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

from genesis_core.engine.state import EventStore, Projector

class ReleaseCommand:
    """Generates a release manifest and emits a release_created event."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)

    def run(self, version: str):
        events = self.store.load_all()
        status = Projector.get_feature_status(events)
        
        # Calculate features included (converged)
        converged_features = [f for f, d in status.items() if all(s == "converged" for s in d["trajectory"].values())]
        
        # Calculate coverage (mocked for now, would use gaps command logic)
        coverage_pct = 100 if converged_features else 0
        
        # Emit Release Event
        self.store.emit(
            "release_created",
            project="unknown",
            data={
                "version": version,
                "features_included": len(converged_features),
                "coverage_pct": coverage_pct,
                "known_gaps": 0
            }
        )
        
        # Write Release Manifest
        manifest_path = self.workspace_root / "snapshots" / f"release_{version}.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": converged_features
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
            
        print(f"Release {version} created. Manifest saved to {manifest_path}")
