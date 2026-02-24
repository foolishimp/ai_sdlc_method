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
from gemini_cli.engine.config_loader import ConfigLoader

def run_iterate_loop(feature, edge, asset, mode, store, workspace_root, depth=0):
    """
    TRULY RECURSIVE iterate() implementation.
    depth: prevents infinite recursion.
    """
    if depth > 3:
        print(f"ERROR: Max recursion depth (3) reached for {feature}")
        return False

    events = store.load_all()
    iter_count = Projector.get_iteration_count(events, feature, edge)
    
    loader = ConfigLoader(workspace_root)
    functors = [DeterministicFunctor(), GeminiFunctor(), HumanFunctor()]
    engine = IterateEngine(functors, constraints=loader.constraints)
    
    if iter_count == 0:
        store.emit("edge_started", "imp_gemini", feature=feature, edge=edge)
    
    asset_path = Path(asset)
    report = engine.run(asset_path, {
        "asset_name": asset,
        "edge": edge,
        "iteration_count": iter_count
    }, mode=mode)
    
    # 1. Check Guardrails
    if any(not g.passed for g in report.guardrail_results):
        print(f"\n[GUARDRAIL BLOCK] {feature} aborted.")
        return False

    # 2. Handle Spawn Requests (ACTUAL RECURSION)
    if report.spawn:
        spawn_req = report.spawn
        child_id = f"{feature}-DISC-{depth+1}"
        print(f"\n[RECURSION L{depth}] LLM requested sub-problem investigation.")
        print(f"Question: {spawn_req.question}")
        
        # Create child vector
        spawn_cmd = SpawnCommand(workspace_root)
        spawn_cmd.run(child_id, intent_id="INT-GEN-001", vector_type=spawn_req.vector_type, parent=feature)
        
        # RECURSIVE CALL: The engine calls itself on the child vector
        print(f"[RECURSION L{depth}] Transferring control to child: {child_id}...")
        # For the child, we iterate on a 'findings' asset
        child_asset = workspace_root / "features" / "active" / f"{child_id}_findings.md"
        child_asset.write_text(f"# Findings for {spawn_req.question}\nImplements: REQ-TEMP")
        
        # Recursively run the loop for the child
        success = run_iterate_loop(child_id, "investigation→findings", str(child_asset), "headless", store, workspace_root, depth + 1)
        
        if success:
            print(f"[RECURSION L{depth}] Child {child_id} converged. Resuming parent {feature}.")
            store.emit("spawn_folded_back", "imp_gemini", feature=feature, data={"child": child_id})
        else:
            print(f"[RECURSION L{depth}] Child {child_id} failed. Parent {feature} remains blocked.")
            return False

    # 3. Record Results
    status = "converged" if report.converged else ("blocked" if report.spawn else "iterating")
    store.emit("iteration_completed", "imp_gemini", 
               feature=feature, 
               edge=edge, 
               delta=report.delta,
               data={"status": status})
    
    if report.converged:
        store.emit("edge_converged", "imp_gemini", feature=feature, edge=edge)
        print(f"Success! {edge} converged.")
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(prog="gemini", description="AI SDLC Cockpit (v2.8)")
    parser.add_argument("--workspace", help="Path to the .ai-workspace root")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("start", help="Detect state and go")
    subparsers.add_parser("status", help="Where am I?")
    
    init_p = subparsers.add_parser("init", help="Initialize workspace")
    init_p.add_argument("--name", required=True)
    
    spawn_p = subparsers.add_parser("spawn", help="Create new feature vector")
    spawn_p.add_argument("--id", required=True)
    spawn_p.add_argument("--intent", required=True)
    spawn_p.add_argument("--type", default="feature")

    iterate_p = subparsers.add_parser("iterate", help="Run iterate() on an edge")
    iterate_p.add_argument("--feature", required=True)
    iterate_p.add_argument("--edge", required=True)
    iterate_p.add_argument("--asset", required=True)
    iterate_p.add_argument("--mode", default="interactive", choices=["interactive", "headless"])

    args = parser.parse_args()
    
    workspace_root = Path(args.workspace) if args.workspace else Path.cwd() / ".ai-workspace"
    store = EventStore(workspace_root)
    
    if args.command == "init":
        InitCommand(workspace_root).run(args.name)
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
        if current_state == ProjectState.IN_PROGRESS:
            feature = state_mgr.get_next_actionable_feature()
            if feature:
                print(f"Next Logical Step: Feature {feature.get('feature')} on {state_mgr.get_next_edge(feature)}")
    elif args.command == "iterate":
        run_iterate_loop(args.feature, args.edge, args.asset, args.mode, store, workspace_root)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
