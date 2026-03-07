# Implements: REQ-UX-003, REQ-UX-005, REQ-TOOL-003
import yaml
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
from gemini_cli.engine.state import Projector, EventStore
from gemini_cli.internal.state_machine import StateManager, ProjectState

class StatusCommand:
    """Provides situational awareness and regenerates STATUS.md."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.project_root = workspace_root.parent
        self.store = EventStore(workspace_root)
        self.state_mgr = StateManager(workspace_root=str(workspace_root.absolute()))

    def run(self):
        events = self.store.load_all()
        status_data = Projector.get_feature_status(events, project_root=self.project_root)
        current_state = self.state_mgr.get_current_state()
        
        print("\nAI SDLC CURRENT STATUS")
        print("="*30)
        print(f"Project State: {current_state.value}")
        
        for feat, data in status_data.items():
            print(f"\nFeature: {feat}")
            for edge, state in data["trajectory"].items():
                marker = "✓" if state == "converged" else "●"
                print(f"  {marker} {edge:<20} {state}")

        # Regenerate STATUS.md
        self._generate_status_md(status_data, current_state, events)
        print(f"\nUpdated {self.workspace_root / 'STATUS.md'}")

    def _generate_status_md(self, status_data: Dict, current_state: ProjectState, events: List[Dict]):
        status_file = self.workspace_root / "STATUS.md"
        
        # 1. Phase Completion Summary
        converged_count = 0
        in_progress_count = 0
        # Reference the v2.8.0 canonical edges for summary
        canonical_edges = [
            "intent→requirements", "requirements→feature_decomp", "feature_decomp→design",
            "design→module_decomp", "module_decomp→basis_proj", "basis_proj→code",
            "code↔unit_tests", "design→test_cases", "module_decomp→uat_tests"
        ]
        
        for feat, data in status_data.items():
            for edge, state in data["trajectory"].items():
                if state == "converged":
                    converged_count += 1
                else:
                    in_progress_count += 1

        # 2. Traceability Coverage (Placeholder for now, could call GapsCommand logic)
        total_reqs = self._count_reqs()
        
        # 3. Process Telemetry
        total_events = len(events)
        last_event_time = events[-1].get("eventTime", "N/A") if events else "N/A"

        content = f"""# Project Status — {self.project_root.name}

Generated: {datetime.now(timezone.utc).isoformat()}
State: {current_state.value}

## Phase Completion Summary
| Metric | Count |
|--------|-------|
| Converged Edges | {converged_count} |
| In-progress Edges | {in_progress_count} |
| Total Events | {total_events} |
| Last Activity | {last_event_time} |

## Feature Trajectory
"""
        for feat, data in status_data.items():
            if data["status"] == "pending":
                continue
            content += f"\n### {feat}: {data.get('title', 'Unknown')}\n"
            content += "| Edge | Status | Iteration (T) | Delta (V) | Hamiltonian (H) | Diagnostic |\n"
            content += "|------|--------|---------------|-----------|-----------------|------------|\n"
            for edge, state_info in data["trajectory"].items():
                if isinstance(state_info, dict):
                    status = state_info.get("status", "unknown")
                    iter_count = state_info.get("iteration", 0)
                    delta = state_info.get("delta", 0)
                    
                    # Compute Hamiltonian
                    h_val = iter_count + delta
                    
                    # Determine Diagnostic Pattern (ADR-S-020)
                    # For simplicity in this view, we just show the current state
                    diagnostic = "Healthy"
                    if status == "blocked": diagnostic = "Blocked"
                    elif delta > 5: diagnostic = "Dense Surface"
                    elif delta == 0: diagnostic = "Converged"
                    
                    content += f"| {edge} | {status} | {iter_count} | {delta} | {h_val} | {diagnostic} |\n"
                else:
                    status = state_info
                    content += f"| {edge} | {status} | N/A | N/A | N/A | N/A |\n"

        content += "\n## Pending Features (from Spec)\n"
        for feat, data in status_data.items():
            if data["status"] == "pending":
                content += f"- **{feat}**: {data.get('title', 'No Title')}\n"

        content += f"""
## Traceability Coverage
- Estimated Requirements: {total_reqs}
- Verified: {converged_count} (Estimated)

## Self-Reflection
- Current State: {current_state.value}
"""
        if current_state == ProjectState.IN_PROGRESS:
            next_feat = self.state_mgr.get_next_actionable_feature()
            if next_feat:
                content += f"- Next Action: Work on {next_feat.get('feature')} edge {self.state_mgr.get_next_edge(next_feat)}\n"

        status_file.write_text(content)

    def _count_reqs(self) -> int:
        count = 0
        spec_dir = self.project_root / "specification"
        if spec_dir.exists():
            for path in spec_dir.glob("*.md"):
                content = path.read_text(errors="ignore")
                count += len(re.findall(r"REQ-[A-Z0-9]+-\d+", content))
        return count
