# Implements: REQ-ITER-001, REQ-ITER-002, REQ-LIFE-008
import re
from pathlib import Path
from datetime import datetime, timezone
from gemini_cli.engine.state import EventStore, Projector
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.functors.f_deterministic import DeterministicFunctor
from gemini_cli.functors.f_probabilistic import GeminiFunctor
from gemini_cli.functors.f_human import HumanFunctor
from gemini_cli.engine.config_loader import ConfigLoader
from gemini_cli.engine.topology import GraphTopology
from gemini_cli.commands.spawn import SpawnCommand

class IterateCommand:
    """Universal Iteration Agent command."""
    
    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.store = EventStore(workspace_root)

    def run(self, feature: str, edge: str, asset: str, mode: str = "interactive", depth: int = 0):
        """Runs the universal iterate() loop on a specific graph edge."""
        return self._run_iterate_loop(feature, edge, asset, mode, depth)

    def _run_iterate_loop(self, feature, edge, asset, mode, depth=0):
        if depth > 3:
            print(f"ERROR: Max recursion depth (3) reached for {feature}")
            return False

        events = self.store.load_all()
        iter_count = Projector.get_iteration_count(events, feature, edge)
        
        loader = ConfigLoader(self.workspace_root, design_name=self.design_name)
        topology = GraphTopology(self.workspace_root)
        
        # 1. Resolve Evaluators from Topology
        transitions = topology.topology.get("transitions", [])
        evaluator_types = ["agent", "human"] # Default
        
        # Normalize input edge by splitting on arrows and taking first/last parts
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
        
        engine = IterateEngine(functors, constraints=loader.constraints, project_root=self.workspace_root.parent)
        
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
            spawn_cmd = SpawnCommand(self.workspace_root)
            spawn_cmd.run(child_id, intent_id="INT-GEN-001", vector_type=spawn_req.vector_type, parent=feature)
            
            # RECURSIVE CALL
            print(f"[RECURSION L{depth}] Transferring control to child: {child_id}...")
            child_asset = self.workspace_root / "features" / "active" / f"{child_id}_findings.md"
            child_asset.write_text(f"# Findings for {spawn_req.question}\nImplements: REQ-TEMP")
            
            success = self._run_iterate_loop(child_id, "investigation\u2192findings", str(child_asset), "headless", depth=depth + 1)
            
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
            # Auto-regenerate STATUS.md
            from gemini_cli.commands.status import StatusCommand
            StatusCommand(self.workspace_root).run()
            return True
        
        return False
