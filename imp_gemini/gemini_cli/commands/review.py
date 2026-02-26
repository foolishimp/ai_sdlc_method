from pathlib import Path
import json
from gemini_cli.engine.state import EventStore

class ReviewCommand:
    """Implements the Review Boundary (REQ-SENSE-005)."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)

    def run(self, action: str = "list", proposal_id: str = None):
        proposals_path = self.workspace_root / "proposals"
        proposals_path.mkdir(exist_ok=True)
        
        if action == "list":
            proposals = list(proposals_path.glob("*.json"))
            if not proposals:
                print("No pending proposals for review.")
                return
            
            print("\nPENDING PROPOSALS")
            print("="*30)
            for p in proposals:
                with open(p) as f:
                    data = json.load(f)
                    print(f"[{p.stem}] {data.get('title', 'No Title')}")
                    print(f"  Source: {data.get('source', 'Unknown')}")
                    print(f"  Severity: {data.get('severity', 'info')}")
                    print("-" * 20)
        
        elif action == "approve" and proposal_id:
            p_file = proposals_path / f"{proposal_id}.json"
            if not p_file.exists():
                print(f"Proposal {proposal_id} not found.")
                return
            
            with open(p_file) as f:
                data = json.load(f)
            
            # Record approval event
            self.store.emit(
                "proposal_approved",
                project="imp_gemini",
                data={"proposal_id": proposal_id, "type": data.get("type")}
            )
            
            # Delete proposal after approval
            p_file.unlink()
            print(f"Proposal {proposal_id} approved and applied.")
            
        elif action == "dismiss" and proposal_id:
            p_file = proposals_path / f"{proposal_id}.json"
            if not p_file.exists():
                print(f"Proposal {proposal_id} not found.")
                return
            
            self.store.emit(
                "proposal_dismissed",
                project="imp_gemini",
                data={"proposal_id": proposal_id}
            )
            p_file.unlink()
            print(f"Proposal {proposal_id} dismissed.")
        else:
            print(f"Unknown action: {action}")
