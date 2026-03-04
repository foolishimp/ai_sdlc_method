# Implements: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-004, REQ-TOOL-005, REQ-TOOL-006, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010, REQ-F-TOOL-001
# Implements: REQ-CLI-001, REQ-CLI-002, REQ-CLI-003, REQ-CLI-004, REQ-CLI-006, REQ-F-GEMINI-CLI-001, REQ-F-UX-001, REQ-F-TOOL-001
"""
Gemini CLI: The Generic SDLC Cockpit.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from gemini_cli.engine.state import EventStore
from gemini_cli.internal.state_machine import StateManager, ProjectState
from gemini_cli.commands.init import InitCommand
from gemini_cli.commands.spawn import SpawnCommand
from gemini_cli.commands.checkpoint import CheckpointCommand
from gemini_cli.commands.trace import TraceCommand
from gemini_cli.commands.gaps import GapsCommand
from gemini_cli.commands.release import ReleaseCommand
from gemini_cli.commands.review import ReviewCommand
from gemini_cli.commands.status import StatusCommand
from gemini_cli.commands.iterate import IterateCommand
from gemini_cli.commands.spec_review import SpecReviewCommand
from gemini_cli.commands.escalate import EscalateCommand
from gemini_cli.commands.zoom import ZoomCommand
from gemini_cli.engine.sensory import SensoryService

def main():
    """AI SDLC Cockpit Entry Point.
    Implements: REQ-UX-001 (Routing), REQ-UX-003 (Status), REQ-UX-004 (Selection)
    """
    parser = argparse.ArgumentParser(prog="gemini", description="AI SDLC Cockpit (v2.8)")
    parser.add_argument("--workspace", help="Path to the .ai-workspace root")
    parser.add_argument("--design", default="gemini_genesis", help="Name of the design tenant")
    subparsers = parser.add_subparsers(dest="command")

    # Start: Detect state and go
    subparsers.add_parser("start", help="Detect state and go")
    
    # Status: Projection of the event log
    subparsers.add_parser("status", help="Where am I?")

    # Spec-review: Review workspace against spec (REQ-LIFE-009)
    subparsers.add_parser("spec-review", help="Review workspace against specification gradient")
    
    # Sense: Run monitors
    sense_parser = subparsers.add_parser("sense", help="Run sensory monitors")
    sense_parser.add_argument("--loop", action="store_true", help="Run in continuous background loop")
    sense_parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds (default: 60)")
    
    # Sync: Resolve context sources
    subparsers.add_parser("sync", help="Sync external context sources")
    
    # Init: Initialize workspace
    init_p = subparsers.add_parser("init", help="Initialize workspace")
    init_p.add_argument("--name", required=True)
    
    # Spawn: Create new feature vector
    spawn_p = subparsers.add_parser("spawn", help="Create new feature vector")
    spawn_p.add_argument("--id", required=True)
    spawn_p.add_argument("--intent", required=True)
    spawn_p.add_argument("--type", default="feature")

    # Iterate: Run the universal engine
    iterate_p = subparsers.add_parser("iterate", help="Run iterate() on an edge")
    iterate_p.add_argument("--feature", required=True)
    iterate_p.add_argument("--edge", required=True)
    iterate_p.add_argument("--asset", required=True)
    iterate_p.add_argument("--mode", default="auto", choices=["interactive", "headless", "auto"])

    # Checkpoint: Save snapshot
    checkpoint_p = subparsers.add_parser("checkpoint", help="Save workspace snapshot")
    checkpoint_p.add_argument("--message", default="Manual Checkpoint")

    # Trace: Show traceability for a REQ key
    trace_p = subparsers.add_parser("trace", help="Show traceability matrix for a REQ key")
    trace_p.add_argument("--key", required=True)

    # Gaps: Scan for gaps
    subparsers.add_parser("gaps", help="Scan for implementation/test gaps")

    # Escalate: Raise convergence issue
    escalate_p = subparsers.add_parser("escalate", help="Escalate convergence issue to human")
    escalate_p.add_argument("--feature", required=True)
    escalate_p.add_argument("--edge", required=True)
    escalate_p.add_argument("--reason", required=True)

    # Zoom: Expand edge into sub-graph
    zoom_p = subparsers.add_parser("zoom", help="Expand edge into sub-graph")
    zoom_p.add_argument("--edge", required=True)

    # Release: Generate release manifest
    release_p = subparsers.add_parser("release", help="Generate a release manifest")
    release_p.add_argument("--version", required=True)

    # Review: Handle sensory proposals (REQ-SENSE-005)
    review_p = subparsers.add_parser("review", help="Review and approve sensory proposals")
    review_p.add_argument("action", choices=["list", "approve", "dismiss"], default="list", nargs="?")
    review_p.add_argument("--id", help="Proposal ID to approve/dismiss")

    args = parser.parse_args()
    
    project_root = Path.cwd()
    workspace_root = Path(args.workspace) if args.workspace else project_root / ".ai-workspace"
    design_name = args.design
    
    if args.command == "init":
        InitCommand(workspace_root).run(args.name, impl=design_name.replace("_genesis", ""))
    elif args.command == "spawn":
        SpawnCommand(workspace_root, design_name=design_name).run(args.id, args.intent, args.type)
    elif args.command == "status":
        StatusCommand(workspace_root).run()
    elif args.command == "spec-review":
        SpecReviewCommand(workspace_root, design_name=design_name).run()
    elif args.command == "sense":
        from gemini_cli.engine.triage import AffectTriageEngine
        service = SensoryService(workspace_root)
        if args.loop:
            # Note: This will block the thread. In a real environment, 
            # this might be run as a daemon or in a separate process.
            service.start_background_service(interval=args.interval)
        else:
            service.run_all_monitors()
            AffectTriageEngine(workspace_root).process_signals()
            print("Sensory monitors executed and signals triaged.")
    elif args.command == "sync":
        from gemini_cli.commands.sync_context import SyncContextCommand
        SyncContextCommand(workspace_root, design_name=design_name).run()
    elif args.command == "start":
        state_mgr = StateManager(workspace_root=str(workspace_root.absolute()))
        current_state = state_mgr.get_current_state()
        print(f"\nDetected State: {current_state.value}")
        if current_state == ProjectState.UNINITIALISED:
            print("Project not initialized. Run /gen-init to bootstrap.")
        elif current_state == ProjectState.NEEDS_INTENT:
            print("Action Required: Define project intent in specification/INTENT.md")
        elif current_state == ProjectState.NO_FEATURES:
            print("Action Required: Spawn your first feature vector using /gen-spawn.")
        elif current_state == ProjectState.IN_PROGRESS:
            feature = state_mgr.get_next_actionable_feature()
            if feature:
                print(f"Next Logical Step: Feature {feature.get('feature')} on {state_mgr.get_next_edge(feature)}")
        elif current_state == ProjectState.ALL_CONVERGED:
            print("All features converged! 🎉 Ready for release.")
        else:
            print(f"Status: {current_state.value}")
    elif args.command == "iterate":
        IterateCommand(workspace_root, design_name=design_name).run(args.feature, args.edge, args.asset, args.mode)
    elif args.command == "checkpoint":
        CheckpointCommand(workspace_root).run(args.message)
    elif args.command == "trace":
        TraceCommand(project_root).run(args.key)
    elif args.command == "gaps":
        impl_name = design_name.replace("_genesis", "")
        current_project_root = workspace_root.parent
        GapsCommand(current_project_root, impl_name=impl_name).run()
    elif args.command == "escalate":
        EscalateCommand(workspace_root, design_name=design_name).run(args.feature, args.edge, args.reason)
    elif args.command == "zoom":
        ZoomCommand(workspace_root).run(args.edge)
    elif args.command == "release":
        ReleaseCommand(workspace_root, design_name=design_name).run(args.version)
    elif args.command == "review":
        ReviewCommand(workspace_root).run(args.action, args.id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
