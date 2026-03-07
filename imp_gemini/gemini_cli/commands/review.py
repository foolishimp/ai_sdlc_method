# Implements: REQ-SENSE-005, REQ-EVOL-004, REQ-EVOL-005, REQ-F-EVOL-001
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from gemini_cli.engine.state import EventStore
from gemini_cli.commands.spawn import SpawnCommand

class ReviewCommand:
    """Implements the Review Boundary (REQ-SENSE-005) and Promotion Phase."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.project_root = workspace_root.parent
        self.store = EventStore(workspace_root)

    def run(self, action: str = "list", proposal_id: str = None):
        events = self.store.load_all()
        # Filter for feature_proposal events (v2 schema: facets.sdlc_event_type.type)
        proposals = []
        for e in events:
            facets = e.get("run", {}).get("facets", {})
            type_facet = facets.get("sdlc_event_type", {})
            if type_facet.get("type") == "feature_proposal":
                proposals.append(e)
        
        # Filter for only latest status of each proposal
        latest_proposals = {}
        for p in proposals:
            data = p.get("_metadata", {}).get("original_data", {})
            pid = data.get("proposal_id")
            if pid:
                latest_proposals[pid] = p

        if action == "list":
            print("\nPENDING FEATURE PROPOSALS")
            print("="*40)
            for pid, p in latest_proposals.items():
                data = p.get("_metadata", {}).get("original_data", {})
                print(f"[{pid}] {data.get('feature_id')}: {data.get('title')}")
                print(f"      Intent: {data.get('intent_id')} | Triggered: {p.get('eventTime')}")
            return

        if not proposal_id:
            print("Error: Action requires --id")
            return

        if proposal_id not in latest_proposals:
            print(f"Error: Proposal {proposal_id} not found.")
            return

        proposal = latest_proposals[proposal_id]

        if action == "approve":
            self._promote_proposal(proposal)
        elif action == "dismiss":
            self.store.emit(
                "proposal_dismissed",
                project="imp_gemini",
                data={"proposal_id": proposal_id}
            )
            print(f"Proposal {proposal_id} dismissed.")

    def _promote_proposal(self, proposal: Dict):
        data = proposal.get("_metadata", {}).get("original_data", {})
        fid = data["feature_id"]
        title = data["title"]
        reqs = data.get("requirements", [])
        
        print(f"Promoting {fid} to Specification Singleton...")

        spec_file = self.project_root / "specification" / "features" / "FEATURE_VECTORS.md"
        if not spec_file.exists():
            print(f"Error: Spec file not found at {spec_file}")
            return

        # 1. Update Singleton Definition (Idempotent append)
        content = spec_file.read_text()
        prev_hash = hashlib.sha256(content.encode()).hexdigest()
        
        if f"### {fid}:" in content:
            print(f"Warning: {fid} already exists in spec. Skipping file write.")
        else:
            new_entry = f"\n---\n\n### {fid}: {title}\n\nGenerated from homeostatic response to {data['intent_id']}.\n\n**Satisfies**: {', '.join(reqs)}\n\n**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩\n"
            content += new_entry
            spec_file.write_text(content)
            
            new_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # 2. Emit spec_modified event
            self.store.emit(
                "spec_modified",
                project="imp_gemini",
                data={
                    "previous_hash": prev_hash,
                    "new_hash": new_hash,
                    "delta": f"Added feature {fid}",
                    "trigger_event_id": proposal.get("eventTime")
                }
            )

        # 3. Inflate Workspace Vector (The "How")
        spawn = SpawnCommand(self.workspace_root)
        spawn.run(fid, intent_id=data["intent_id"], vector_type="feature")
        
        # 4. Emit proposal_approved
        self.store.emit(
            "proposal_approved",
            project="imp_gemini",
            data={"proposal_id": data["proposal_id"], "feature_id": fid}
        )
        
        print(f"Successfully promoted {fid}. Operational trajectory initialized.")
        
        # 5. Git Integration (Optional/Requested)
        self._git_commit(fid, data["proposal_id"])

    def _git_commit(self, fid: str, pid: str):
        try:
            import subprocess
            subprocess.run(["git", "add", "specification/features/FEATURE_VECTORS.md"], cwd=self.project_root)
            msg = f"feat: Promote proposal {pid} ({fid}) to specification"
            subprocess.run(["git", "commit", "-m", msg], cwd=self.project_root)
            print(f"Git commit created: {msg}")
        except Exception as e:
            print(f"Git commit failed: {e}")
