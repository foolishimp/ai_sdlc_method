import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from genesis_core.engine.iterate import IterateEngine
from genesis_core.engine.models import FunctorResult, Outcome
from gemini_cloud.engine.state import CloudEventStore
from gemini_cloud.functors.f_vertex import VertexFunctor

class CloudHumanFunctor:
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        print("\n[CLOUD REVIEW] Manual check required.")
        choice = input("Approve? (y/n): ")
        return FunctorResult(
            name="cloud_human",
            outcome=Outcome.PASS if choice == "y" else Outcome.FAIL,
            delta=0 if choice == "y" else 1,
            reasoning="Manual cloud approval."
        )

def main():
    parser = argparse.ArgumentParser(prog="gemini-cloud", description="AI SDLC Cloud Cockpit")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--project", required=True)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show project status from Firestore")
    
    iterate_p = subparsers.add_parser("iterate", help="Run cloud-native iterate()")
    iterate_p.add_argument("--feature", required=True)
    iterate_p.add_argument("--edge", required=True)
    iterate_p.add_argument("--candidate", required=True)
    iterate_p.add_argument("--mode", default="headless")

    args = parser.parse_args()
    
    db = None 
    store = CloudEventStore(db, args.tenant, args.project)
    
    if args.command == "status":
        print(f"\nAI SDLC CLOUD STATUS — {args.project}")
        print("="*40)
        print("Materializing view from Firestore...")
        
    elif args.command == "iterate":
        functors = [VertexFunctor(args.project), CloudHumanFunctor()]
        engine = IterateEngine(functors)
        
        store.emit("edge_started", feature=args.feature, edge=args.edge)
        asset_path = Path(args.candidate)
        result = engine.run(asset_path, {"project_id": args.project}, mode=args.mode)
        
        if result.spawn:
            spawn_req = result.spawn
            child_id = f"{args.feature}-DISC-{int(datetime.now().timestamp())}"
            print(f"\n[CLOUD RECURSION] Spawning {child_id}")
            store.emit("feature_spawned", feature=args.feature, data={"child": child_id, "reason": spawn_req.question})

        status = "converged" if result.converged else ("blocked" if result.spawn else "iterating")
        store.emit("iteration_completed", feature=args.feature, edge=args.edge, delta=result.delta, data={"status": status})
        
        if result.converged:
            store.emit("edge_converged", feature=args.feature, edge=args.edge)
            print(f"Success! {args.edge} converged.")
        else:
            print(f"Cloud Iteration Complete. Delta: {result.delta}")

if __name__ == "__main__":
    main()
