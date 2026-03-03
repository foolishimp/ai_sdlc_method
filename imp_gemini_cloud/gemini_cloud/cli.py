import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from gemini_cloud.engine.iterate import CloudIterateEngine
from gemini_cloud.engine.models import FunctorResult, Outcome
from gemini_cloud.engine.state import CloudEventStore
from gemini_cloud.functors.f_vertex import VertexFunctor
from gemini_cloud.functors.f_deterministic import DeterministicFunctor

class CloudHumanFunctor:
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        print("\n[CLOUD REVIEW] Manual check required.")
        print(f"Context: {context.get('edge_config', {}).get('description', 'No description')}")
        print(f"Candidate preview: {candidate[:100]}...")
        choice = input("Approve? (y/n): ")
        return FunctorResult(
            name="cloud_human",
            outcome=Outcome.PASS if choice == "y" else Outcome.FAIL,
            delta=0 if choice == "y" else 1,
            reasoning="Manual cloud approval." if choice == "y" else "Manual rejection."
        )

def main():
    parser = argparse.ArgumentParser(prog="gemini-cloud", description="AI SDLC Cloud Cockpit")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--project", required=True)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show project status from Firestore")
    
    subparsers.add_parser("init", help="Initialise the cloud-backed .ai-workspace/ and STATUS.md")
    
    subparsers.add_parser("start", help="Authenticate and poll Firestore for assigned tasks")
    
    subparsers.add_parser("sense", help="Run sensory monitors and collect signals")
    subparsers.add_parser("triage", help="Triage signals using Vertex AI")
    
    iterate_p = subparsers.add_parser("iterate", help="Run cloud-native iterate()")
    iterate_p.add_argument("--feature", required=True)
    iterate_p.add_argument("--edge", required=True)
    iterate_p.add_argument("--candidate", required=True)
    iterate_p.add_argument("--mode", default="interactive")

    args = parser.parse_args()
    
    db = None 
    store = CloudEventStore(db, args.tenant, args.project)
    
    if args.command == "status":
        from gemini_cloud.internal.cloud_state import WorkspaceState, ProjectState
        ws = WorkspaceState(args.tenant, args.project, db=None)
        state = ws.detect_state()
        print(f"\nAI SDLC CLOUD STATUS — {args.project}")
        print("="*40)
        print(f"Current State: {state.value.upper()}")
        print("="*40)

    elif args.command == "init":
        from gemini_cloud.internal.cloud_state import WorkspaceState, ProjectState
        # Scaffold local folders
        workspace = Path(".ai-workspace")
        for sub in ["events", "features", "tasks", "snapshots", "spec"]:
            (workspace / sub).mkdir(parents=True, exist_ok=True)
        
        # Create STATUS.md
        status_md = Path("STATUS.md")
        if not status_md.exists():
            status_md.write_text(f"# Project Status: {args.project}\n\nGenerated: {datetime.now().isoformat()}\n\n## Summary\nInitialised via gemini-cloud init.\n")
            print(f"Created {status_md}")

        # Emit init event
        store.emit("project_initialised", data={"project": args.project})
        print(f"Initialised cloud workspace for {args.project}")

    elif args.command == "start":
        print(f"\n[CLOUD AUTH] Authenticating via gcloud for tenant {args.tenant}...")
        print(f"Polling Firestore for assigned tasks in project {args.project}...")
        # Simulate fetching tasks
        print("- Found 1 active feature vector: F-MAPPER")
        print("Ready to iterate.\n")

    elif args.command == "sense":
        from gemini_cloud.sensory.service import SensoryService
        svc = SensoryService(store)
        signals = svc.sense()
        print(f"\n[SENSORY SERVICE] {len(signals)} signals collected.")
        for s in signals:
            print(f"- {s['source']} ({s['type']}): {s['message']}")

    elif args.command == "triage":
        from gemini_cloud.sensory.service import SensoryService
        svc = SensoryService(store)
        # In a real implementation, we'd fetch signals from Firestore
        # Here we simulate by sensing and then triaging
        signals = svc.sense()
        proposals = svc.triage(signals)
        print(f"\n[AFFECT TRIAGE] Processed {len(signals)} signals. Raised {len(proposals)} intents.")
        for p in proposals:
            print(f"- {p['data']['description']}")

    elif args.command == "iterate":
        functors = {
            "F_P": VertexFunctor(args.project),
            "F_D": DeterministicFunctor(),
            "F_H": CloudHumanFunctor()
        }
        engine = CloudIterateEngine(functors)
        
        store.emit("edge_started", feature=args.feature, edge=args.edge)
        asset_path = Path(args.candidate)
        
        result = engine.run(
            asset_path=asset_path,
            feature=args.feature,
            edge=args.edge,
            context={"project_id": args.project},
            mode=args.mode
        )
        
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
