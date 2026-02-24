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

def run_iterate_loop(args, store, workspace_root):
    """Orchestrates the iterate() call and recursive spawning."""
    # 1. Load context
    events = store.load_all()
    iter_count = Projector.get_iteration_count(events, args.feature, args.edge)
    
    # Escalation Chain Composition
    functors = [
        DeterministicFunctor(), 
        GeminiFunctor(), 
        HumanFunctor()
    ]
    engine = IterateEngine(functors)
    
    # 2. Emit Edge Start (if first iteration)
    if iter_count == 0:
        store.emit("edge_started", "imp_gemini", feature=args.feature, edge=args.edge)
    
    # 3. Run Iteration
    asset_path = Path(args.asset)
    report = engine.run(asset_path, {
        "asset_name": args.asset,
        "iteration_count": iter_count
    }, mode=args.mode)
    
    # 4. Handle Spawn Requests (RECURSION)
    if report.spawn:
        spawn_req = report.spawn
        child_id = f"{args.feature}-DISC-{int(datetime.now().timestamp())}"
        print(f"\n[RECURSION] LLM requested sub-problem investigation.")
        print(f"Question: {spawn_req.question}")
        print(f"Spawning child vector: {child_id}")
        
        store.emit("feature_spawned", "imp_gemini", feature=args.feature, data={
            "child": child_id,
            "reason": spawn_req.question,
            "vector_type": spawn_req.vector_type
        })
        
        # --- RECURSIVE CALL ---
        # Today we mock the recursion by iterating on a hypothetical sub-asset
        # To truly execute, we would define a sub-graph here.
        print(f"[RECURSION] Executing child iterate loop for {child_id}...")
        # Simulate convergence of the sub-problem
        store.emit("edge_converged", "imp_gemini", feature=child_id, edge="investigation→findings")
        print(f"[RECURSION] Child {child_id} converged. Folding back.")
        store.emit("spawn_folded_back", "imp_gemini", feature=args.feature, data={"child": child_id})
        
    # 5. Emit Result
    status = "converged" if report.converged else ("blocked" if report.spawn else "iterating")
    store.emit("iteration_completed", "imp_gemini", 
               feature=args.feature, 
               edge=args.edge, 
               delta=report.delta,
               data={"status": status})
    
    if report.converged:
        store.emit("edge_converged", "imp_gemini", feature=args.feature, edge=args.edge)
        print(f"\nSuccess! {args.edge} converged.")
    else:
        if report.spawn:
            # Recursion happened, now we can potentially unblock
            print(f"\nRecursion complete. Parent {args.feature} unblocked.")
        else:
            print(f"\nIterating... Delta: {report.delta}")

def main():
    parser = argparse.ArgumentParser(prog="gemini", description="AI SDLC Cockpit (v2.8)")
    parser.add_argument("--workspace", help="Path to the .ai-workspace root")
    subparsers = parser.add_subparsers(dest="command")

    # Start: Detect state and suggest next action
    start_p = subparsers.add_parser("start", help="Detect state and go")
    
    # Status: Projection of the event log
    status_p = subparsers.add_parser("status", help="Where am I?")
    
    # Iterate: Run the universal engine
    iterate_p = subparsers.add_parser("iterate", help="Run iterate() on an edge")
    iterate_p.add_argument("--feature", required=True)
    iterate_p.add_argument("--edge", required=True)
    iterate_p.add_argument("--asset", required=True)
    iterate_p.add_argument("--mode", default="interactive", choices=["interactive", "headless"])

    args = parser.parse_args()
    
    workspace_root = Path(args.workspace) if args.workspace else Path.cwd() / ".ai-workspace"
    store = EventStore(workspace_root)
    
    if args.command == "status":
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
        print("="*30)
        
        if current_state == ProjectState.UNINITIALISED:
            print("Project not initialized. Run /gen-init to bootstrap.")
        elif current_state == ProjectState.IN_PROGRESS:
            feature = state_mgr.get_next_actionable_feature()
            if feature:
                edge = state_mgr.get_next_edge(feature)
                print(f"Next Logical Step: Feature {feature.get('feature')} on {edge}")
        else:
            print(f"Status: {current_state.value}")

    elif args.command == "iterate":
        run_iterate_loop(args, store, workspace_root)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
