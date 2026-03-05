# Implements: ADR-S-015, ADR-S-016
from pathlib import Path
from typing import List, Dict, Any
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.engine.state import EventStore

class CheckpointCommand:
    """Wraps external filesystem changes (human or other) into formal transactions.
    Heals the integrity gaps between the actual filesystem and the Event Ledger.
    """
    
    def __init__(self, workspace_root: Path, project_root: Path = None):
        self.workspace_root = workspace_root
        self.project_root = project_root or workspace_root.parent
        self.store = EventStore(self.workspace_root)
        self.engine = IterateEngine(functor_map={}, project_root=self.project_root)

    def run(self, feature_id: str = "GLOBAL", edge: str = "human_edit", description: str = "Manual checkpoint", heal_tx: bool = False):
        print(f"\n  [CHECKPOINT] Scanning for uncommitted changes in {self.project_root.name}...")
        
        gaps = self.engine.detect_integrity_gaps()
        
        if not gaps:
            print("  [CHECKPOINT] No gaps detected. Ledger is in sync with filesystem.")
            return

        uncommitted = [g for g in gaps if g["type"] == "UNCOMMITTED_CHANGE"]
        missing = [g for g in gaps if g["type"] == "MISSING_ARTIFACT"]
        open_tx = [g for g in gaps if g["type"] == "OPEN_TRANSACTION"]

        print(f"  [CHECKPOINT] Found {len(uncommitted)} uncommitted changes, {len(missing)} missing artifacts, and {len(open_tx)} open transactions.")
        
        if not uncommitted and not missing and not (heal_tx and open_tx):
            return

        # 1. Resolve Open Transactions if requested
        if heal_tx and open_tx:
            print(f"  [CHECKPOINT] Aborting {len(open_tx)} orphaned transactions...")
            for tx in open_tx:
                self.store.emit(
                    event_type="transaction_aborted",
                    project=self.project_root.name,
                    feature="RECOVERY",
                    edge="cleanup",
                    data={"reason": "Manual cleanup of orphaned transaction", "original_run_id": tx["run_id"]},
                    eventType="ABORT",
                    parent_run_id=tx["run_id"]
                )

        # 2. Archive and Bless uncommitted changes
        if uncommitted or missing:
            print(f"  [CHECKPOINT] Archiving current state...")
            self.engine._archive_iteration(feature_id, edge, iteration=0, failed=False)

            changed_paths = [Path(self.project_root / g["path"]) for g in uncommitted]
            print(f"  [CHECKPOINT] Blessing {len(changed_paths)} files into the ledger...")
            
            self.store.emit(
                event_type="checkpoint_committed",
                project=self.project_root.name,
                feature=feature_id,
                edge=edge,
                delta=0,
                data={
                    "regime": "human",
                    "description": description,
                    "gap_count": len(gaps)
                },
                eventType="COMPLETE",
                outputs=changed_paths
            )

        print(f"  [CHECKPOINT] SUCCESS: Ledger updated. Unit of Work committed.")
