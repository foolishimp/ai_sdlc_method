# Implements: REQ-CLI-001, REQ-CLI-002, REQ-CLI-003, REQ-CLI-004
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
                
    elif args.command == "iterate":
        # 1. Load context from event log
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
        result = engine.run(asset_path, {
            "asset_name": args.asset,
            "iteration_count": iter_count
        }, mode=args.mode)
        
        # 4. Handle Spawn Requests (Recursion)
        if result.get("spawn"):
            spawn_req = result["spawn"]
            child_id = f"{args.feature}-DISC-{int(datetime.now().timestamp())}"
            print("\n[RECURSION] LLM requested sub-problem investigation.")
            print(f"Question: {spawn_req.question}")
            print(f"Spawning child vector: {child_id}")
            
            store.emit("feature_spawned", "imp_gemini", feature=args.feature, data={
                "child": child_id,
                "reason": spawn_req.question,
                "vector_type": spawn_req.vector_type
            })
            
        # 5. Emit Result
        status = "converged" if result["converged"] else ("blocked" if result.get("spawn") else "iterating")
        store.emit("iteration_completed", "imp_gemini", 
                   feature=args.feature, 
                   edge=args.edge, 
                   data={"delta": result["delta"], "status": status})
        
        if result["converged"]:
            store.emit("edge_converged", "imp_gemini", feature=args.feature, edge=args.edge)
            print(f"\nSuccess! {args.edge} converged.")
        else:
            if result.get("spawn"):
                print(f"\nBlocked! Waiting for recursion result. Delta: {result['delta']}")
            else:
                print(f"\nIterating... Delta: {result['delta']}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
