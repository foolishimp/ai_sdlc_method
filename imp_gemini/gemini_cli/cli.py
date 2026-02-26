# Implements: REQ-CLI-001, REQ-CLI-002, REQ-CLI-003, REQ-CLI-004, REQ-CLI-006
"""
Gemini CLI: The Generic SDLC Cockpit.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from gemini_cli.engine.state import EventStore, Projector
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.functors.f_deterministic import DeterministicFunctor
from gemini_cli.functors.f_probabilistic import GeminiFunctor
from gemini_cli.functors.f_human import HumanFunctor
from gemini_cli.internal.state_machine import StateManager, ProjectState
from gemini_cli.commands.init import InitCommand
from gemini_cli.commands.spawn import SpawnCommand
from gemini_cli.commands.checkpoint import CheckpointCommand
from gemini_cli.commands.trace import TraceCommand
from gemini_cli.commands.gaps import GapsCommand
from gemini_cli.commands.release import ReleaseCommand
from gemini_cli.commands.review import ReviewCommand
from gemini_cli.engine.config_loader import ConfigLoader

from gemini_cli.engine.topology import GraphTopology

def run_iterate_loop(feature, edge, asset, mode, store, workspace_root, design_name="gemini_genesis", depth=0):
    """
    TRULY RECURSIVE iterate() implementation.
    depth: prevents infinite recursion.
    """
    if depth > 3:
        print(f"ERROR: Max recursion depth (3) reached for {feature}")
        return False

    events = store.load_all()
    iter_count = Projector.get_iteration_count(events, feature, edge)
    
    loader = ConfigLoader(workspace_root, design_name=design_name)
    topology = GraphTopology(workspace_root)
    
    # 1. Resolve Evaluators from Topology
    transitions = topology.topology.get("transitions", [])
    evaluator_types = ["agent", "human"] # Default
    
    # Normalize input edge by splitting on arrows and taking first/last parts
    import re
    edge_parts = re.split(r"->|\u2192|\u2194", edge)
    src_input = edge_parts[0].strip().lower()
    tgt_input = edge_parts[-1].strip().lower()
    
    for t in transitions:
        src_topo = t.get("source", "").lower()
        tgt_topo = t.get("target", "").lower()
        name_topo = t.get("name", "").lower()
        
        # Match by nodes OR by name
        if (src_input == src_topo and tgt_input == tgt_topo) or \
           (edge.lower() in name_topo or name_topo in edge.lower()):
            evaluator_types = t.get("evaluators", evaluator_types)
            break
    
    print(f"  [TOPOLOGY] Edge {edge} resolved to evaluators: {evaluator_types}")
    
    functor_map = {
        "deterministic": DeterministicFunctor(),
        "agent": GeminiFunctor(),
        "human": HumanFunctor()
    }
    functors = [functor_map[et] for et in evaluator_types if et in functor_map]
    
    engine = IterateEngine(functors, constraints=loader.constraints, project_root=workspace_root.parent)
    
    if iter_count == 0:
        engine.emit_event("edge_started", feature=feature, edge=edge, data={})
    
    asset_path = Path(asset)
    report = engine.run(asset_path, {
        "asset_name": asset,
        "edge": edge,
        "iteration_count": iter_count
    }, mode=mode)
    
    # 2. Check Guardrails
    if any(not g.passed for g in report.guardrail_results):
        print(f"\n[GUARDRAIL BLOCK] {feature} aborted.")
        return False

    # 3. Handle Spawn Requests (ACTUAL RECURSION)
    if report.spawn:
        spawn_req = report.spawn
        child_id = f"{feature}-DISC-{depth+1}"
        print(f"\n[RECURSION L{depth}] LLM requested sub-problem investigation.")
        print(f"Question: {spawn_req.question}")
        
        # Create child vector
        spawn_cmd = SpawnCommand(workspace_root)
        spawn_cmd.run(child_id, intent_id="INT-GEN-001", vector_type=spawn_req.vector_type, parent=feature)
        
        # RECURSIVE CALL
        print(f"[RECURSION L{depth}] Transferring control to child: {child_id}...")
        child_asset = workspace_root / "features" / "active" / f"{child_id}_findings.md"
        child_asset.write_text(f"# Findings for {spawn_req.question}\nImplements: REQ-TEMP")
        
        success = run_iterate_loop(child_id, "investigation\u2192findings", str(child_asset), "headless", store, workspace_root, design_name=design_name, depth=depth + 1)
        
        if success:
            print(f"[RECURSION L{depth}] Child {child_id} converged. Resuming parent {feature}.")
            engine.emit_event("spawn_folded_back", feature=feature, edge=edge, data={"child": child_id})
        else:
            print(f"[RECURSION L{depth}] Child {child_id} failed. Parent {feature} remains blocked.")
            return False

    # 4. Record Results
    status = "converged" if report.converged else ("blocked" if report.spawn else "iterating")
    engine.emit_event("iteration_completed", feature=feature, edge=edge, data={"delta": report.delta, "status": status})
    
    # REQ-LIFE-008: Mandatory side effect - Update Feature Vector
    engine.update_feature_vector(feature, edge, iter_count + 1, status, report.delta, asset_path=str(asset_path))
    
    if report.converged:
        engine.emit_event("edge_converged", feature=feature, edge=edge, data={})
        print(f"Success! {edge} converged.")
        return True
    
    return False

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
    iterate_p.add_argument("--mode", default="interactive", choices=["interactive", "headless"])

    # Checkpoint: Save snapshot
    checkpoint_p = subparsers.add_parser("checkpoint", help="Save workspace snapshot")
    checkpoint_p.add_argument("--message", default="Manual Checkpoint")

    # Trace: Show traceability for a REQ key
    trace_p = subparsers.add_parser("trace", help="Show traceability matrix for a REQ key")
    trace_p.add_argument("--key", required=True)

    # Gaps: Scan for gaps
    subparsers.add_parser("gaps", help="Scan for implementation/test gaps")

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
    store = EventStore(workspace_root)
    
    if args.command == "init":
        InitCommand(workspace_root).run(args.name, impl=design_name.replace("_genesis", ""))
    elif args.command == "spawn":
        SpawnCommand(workspace_root).run(args.id, args.intent, args.type)
    elif args.command == "status":
        events = store.load_all()
        status = Projector.get_feature_status(events)
        print("\nAI SDLC CURRENT STATUS")
        print("="*30)
        for feat, data in status.items():
            print(f"\nFeature: {feat}")
            for edge, state in data["trajectory"].items():
                marker = "✓" if state == "converged" else "●"
                print(f"  {marker} {edge:<20} {state}")
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
        run_iterate_loop(args.feature, args.edge, args.asset, args.mode, store, workspace_root, design_name=design_name)
    elif args.command == "checkpoint":
        CheckpointCommand(workspace_root).run(args.message)
    elif args.command == "trace":
        TraceCommand(project_root).run(args.key)
    elif args.command == "gaps":
        impl_name = design_name.replace("_genesis", "")
        # project_root should be the parent of .ai-workspace
        current_project_root = workspace_root.parent
        GapsCommand(current_project_root, impl_name=impl_name).run()
    elif args.command == "release":
        ReleaseCommand(workspace_root).run(args.version)
    elif args.command == "review":
        ReviewCommand(workspace_root).run(args.action, args.id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
