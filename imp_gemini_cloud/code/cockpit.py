# Implements: REQ-UX-003, REQ-UX-005
"""Gemini Cloud Cockpit - Real-time Project Observability.

Entry point for UJ-3 (Resume & Orient) in the GCP environment.
"""

import argparse
import sys
from typing import Dict, Any

from internal.cloud_state import WorkspaceState, ProjectState

def print_status(state: WorkspaceState):
    """Render the cockpit view."""
    project_state = state.detect_state()
    
    print("
" + "="*60)
    print(f"  Gemini Cloud Cockpit — {state.project_id}")
    print("="*60)
    print(f"  State: {project_state.value}")
    print("-" * 60)

    features = state.get_active_features()
    if not features:
        print("  No active features discovered in Firestore.")
    else:
        print("  You Are Here:")
        for fv in features:
            fid = fv.get("feature", "UNKNOWN")
            markers = state.get_you_are_here(fv)
            print(f"    {fid:<15} intent ✓ → {markers}")

    print("-" * 60)
    print("  Next Action (Suggested):")
    if project_state == ProjectState.UNINITIALISED:
        print("    Run: gcloud functions call gen-init")
    elif project_state == ProjectState.NO_FEATURES:
        print("    Run: cockpit spawn --type feature")
    else:
        print("    Run: gcloud workflows run iterate-engine")
    print("="*60 + "
")

def main():
    parser = argparse.ArgumentParser(description="Gemini Cloud Cockpit")
    parser.add_argument("--tenant", required=True, help="Tenant/Organization ID")
    parser.add_argument("--project", required=True, help="Project ID")
    parser.add_argument("--live", action="store_true", help="Enable real-time updates (Firestore Listeners)")
    
    args = parser.parse_args()

    # In a real environment, we would initialize the Firestore client here
    # db = firestore.Client()
    db = None 

    workspace = WorkspaceState(tenant_id=args.tenant, project_id=args.project, db=db)
    
    if args.live:
        print("Starting live cockpit (listening for Firestore events)...")
        # Logic for firestore.on_snapshot() would go here
    else:
        print_status(workspace)

if __name__ == "__main__":
    main()
