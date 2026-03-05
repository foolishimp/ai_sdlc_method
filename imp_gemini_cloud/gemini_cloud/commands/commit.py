# Implements: ADR-S-015, ADR-S-016
from pathlib import Path
from typing import List, Dict, Any
from gemini_cloud.engine.iterate import CloudIterateEngine
from gemini_cloud.engine.state import CloudEventStore

class CloudCommitCommand:
    """Cloud-native commit command for blessing uncommitted Firestore state."""
    
    def __init__(self, db, tenant_id: str, project_id: str, project_root: Path):
        self.project_root = project_root
        self.store = CloudEventStore(db, tenant_id, project_id, project_root=project_root)
        self.engine = CloudIterateEngine(functors={}, project_root=self.project_root, store=self.store)

    def run(self, feature_id: str = "GLOBAL", edge: str = "manual_edit", description: str = "Cloud manual commit", heal_tx: bool = False):
        print(f"\n  [CLOUD-COMMIT] Scanning for uncommitted changes in {self.project_root.name}...")
        
        # Load all events from Firestore (logic would be here in full impl)
        events = [] 
        
        gaps = self.engine.detect_integrity_gaps(events)
        
        if not gaps:
            print("  [CLOUD-COMMIT] No gaps detected.")
            return

        uncommitted = [g for g in gaps if g["type"] == "UNCOMMITTED_CHANGE"]
        print(f"  [CLOUD-COMMIT] Found {len(uncommitted)} uncommitted changes.")
        
        if uncommitted:
            print(f"  [CLOUD-COMMIT] Archiving and Committing...")
            self.engine._archive_iteration(feature_id, edge, iteration=0, failed=False)
            
            changed_paths = [Path(self.project_root / g["path"]) for g in uncommitted]
            
            self.store.emit(
                event_type="manual_commit",
                feature=feature_id,
                edge=edge,
                delta=0,
                data={"regime": "human", "description": description},
                eventType="COMPLETE",
                outputs=changed_paths
            )
            print(f"  [CLOUD-COMMIT] SUCCESS: Cloud Ledger updated.")
