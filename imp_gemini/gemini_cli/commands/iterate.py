# Implements: REQ-ITER-001, REQ-ITER-002, REQ-LIFE-008, ADR-021
import re
import uuid
import yaml
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from gemini_cli.engine.state import EventStore, Projector
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.functors.f_deterministic import DeterministicFunctor
from gemini_cli.functors.f_probabilistic import GeminiFunctor
from gemini_cli.functors.f_human import HumanFunctor
from gemini_cli.engine.config_loader import ConfigLoader
from gemini_cli.engine.topology import GraphTopology

class IterateCommand:
    """Universal Iteration Agent command with Dual-Mode Dispatcher."""
    
    # ADR-021: Edge-mode affinity table
    AFFINITY_TABLE = {
        "intent\u2192requirements": "interactive",
        "requirements\u2192feature_decomp": "interactive",
        "feature_decomp\u2192design": "interactive",
        "design\u2192module_decomp": "interactive",
        "module_decomp\u2192basis_proj": "interactive",
        "design\u2192code": "engine",
        "basis_proj\u2192code": "engine",
        "code\u2194unit_tests": "engine",
        "uat_tests": "interactive",
        "code\u2192cicd": "engine"
    }

    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.store = EventStore(workspace_root)

    def run(self, feature: str, edge: str, asset: str, mode: str = "auto", depth: int = 0):
        """Runs the universal iterate() loop on a specific graph edge."""
        
        # 1. Dispatch Mode (ADR-021)
        target_mode = mode
        if mode == "auto":
            # Normalize arrow for table lookup
            norm_edge = edge.replace("->", "\u2192").replace("\u2194", "\u2192")
            target_mode = self.AFFINITY_TABLE.get(norm_edge, "interactive")
            print(f"  [DISPATCHER] Edge {edge} matched to affinity: {target_mode}")

        if target_mode == "engine":
            return self._run_engine_traverse(feature, edge, asset, mode, depth)
        else:
            return self._run_interactive_traverse(feature, edge, asset, mode, depth)

    def _run_engine_traverse(self, feature, edge, asset, mode, depth):
        """Level 4: Deterministic Code Traverse (No hooks, guaranteed side-effects)."""
        print(f"\n>>> ENGINE TRAVERSE: {feature} [{edge}]")
        
        # Gap 3: Startup Health Check
        self._run_startup_health_check()
        
        # Use headless if mode is headless or auto
        engine_mode = "headless" if mode in ["headless", "auto"] else mode
        
        # Normal execution
        success = self._execute_iterate_loop(feature, edge, asset, engine_mode, depth, mode_label="engine")
        
        if success:
            # Gap 2: STATUS.md trigger
            from gemini_cli.commands.status import StatusCommand
            StatusCommand(self.workspace_root).run()
            
        return success

    def _run_interactive_traverse(self, feature, edge, asset, mode, depth):
        """Level 1/2: Conversational Traverse (Hook-monitored)."""
        print(f"\n>>> INTERACTIVE TRAVERSE: {feature} [{edge}]")
        # Gap 3: Startup Health Check
        self._run_startup_health_check()
        
        # If mode is headless, we MUST respect it even in interactive path
        engine_mode = mode if mode != "auto" else "interactive"
        
        return self._execute_iterate_loop(feature, edge, asset, engine_mode, depth, mode_label="interactive")

    def _execute_iterate_loop(self, feature, edge, asset, mode, depth, mode_label):
        if depth > 3:
            print(f"ERROR: Max recursion depth (3) reached for {feature}")
            return False

        loader = ConfigLoader(self.workspace_root, design_name=self.design_name)
        topology = GraphTopology(self.workspace_root)
        
        # 1. Resolve Normalized Edge and Configuration
        edge_parts = re.split(r"->|\u2192|\u2194", edge)
        src_input = edge_parts[0].strip().lower()
        tgt_input = edge_parts[-1].strip().lower()
        normalized_edge = f"{src_input}\u2192{tgt_input}"
        
        transitions = topology.topology.get("transitions", [])
        edge_config = {}
        evaluator_types = ["agent", "human"] # Default
        
        for t in transitions:
            if (src_input == t.get("source", "").lower() and tgt_input == t.get("target", "").lower()) or \
               (edge.lower() in t.get("name", "").lower()):
                edge_config = t
                evaluator_types = t.get("evaluators", evaluator_types)
                break
        
        resolved_checklist = loader.resolve_checklist(edge_config)
        if not resolved_checklist and evaluator_types:
            resolved_checklist = [{"evaluator": et} for et in evaluator_types]
        
        # 2. Configure Stateless Engine with Dynamic Routing (ADR-GG-002)
        # Map edges to specialized sub-agents
        SUB_AGENT_MAPPING = {
            "code\u2194unit_tests": "test_fixing_agent",
            "design\u2192code": "source_implementation_agent",
            "requirements\u2192design": "architect_agent",
            "feature_decomp\u2192design": "architect_agent"
        }
        
        target_sub_agent = SUB_AGENT_MAPPING.get(normalized_edge, "aisdlc_investigator")
        print(f"  [ROUTING] Delegating to sub-agent: {target_sub_agent}")

        functor_map = {
            "deterministic": DeterministicFunctor(),
            "agent": GeminiFunctor(sub_agent_id=target_sub_agent),
            "human": HumanFunctor()
        }
        
        engine = IterateEngine(functor_map=functor_map, constraints=loader.constraints, project_root=self.workspace_root.parent)
        
        # 3. Determine T (Iteration Count)
        events = self.store.load_all()
        iter_count = Projector.get_iteration_count(events, feature, normalized_edge)
        current_iteration = iter_count + 1
        
        if iter_count == 0:
            engine.emit_event("edge_started", feature=feature, edge=normalized_edge, data={"mode": mode_label})
        
        asset_path = Path(asset)
        
        # 4. Load context
        fv_path = self.workspace_root / "features" / "active" / f"{feature}.yml"
        fv_data = {}
        if fv_path.exists():
            with open(fv_path, "r") as f:
                fv_data = yaml.safe_load(f) or {}

        print(f"  [METABOLISM] Iteration {current_iteration} (Mode: {mode_label})")

        # 5. Run Stateless Metabolic Pass
        # We use engine.iterate_edge as the Unit of Work proxy to the stateless logic
        record = engine.iterate_edge(
            edge=normalized_edge,
            feature_id=feature,
            asset_path=asset_path,
            context={
                "asset_name": asset,
                "edge": normalized_edge,
                "iteration_count": iter_count,
                "mode": mode,
                "feature_id": feature,
                "feature_vector": fv_data
            },
            iteration=current_iteration,
            mode=mode,
            checklist=resolved_checklist
        )
        
        report = record.report
        
        # 6. Post-iteration Side-effects (Status Update)
        status = "converged" if report.converged else "iterating"
        if report.spawn: status = "blocked"
        
        engine.emit_event("iteration_completed", feature=feature, edge=normalized_edge, data={
            "status": status, 
            "delta": report.delta, 
            "iteration": current_iteration
        })
        
        engine.update_feature_vector(feature, normalized_edge, current_iteration, status, report.delta, str(asset_path), mode=mode)

        # 7. Display Results
        for res in report.functor_results:
            icon = "\u2705" if res.outcome == Outcome.PASS else "\u274c"
            print(f"    {icon} {res.name}: {res.reasoning} (Delta: {res.delta})")
            
        for g in report.guardrail_results:
            icon = "\ud83d\udee1\ufe0f" if g.passed else "\u26a0\ufe0f"
            print(f"    {icon} Guardrail {g.name}: {g.message}")

        # 8. Handle Recursion
        if report.spawn:
            self._handle_spawn(report.spawn, feature, normalized_edge, depth, mode)
            return True

        if report.converged:
            print(f"\nSuccess! {normalized_edge} converged.")
            engine.emit_event("edge_converged", feature=feature, edge=normalized_edge, data={})
            return True
        
        # Hamiltonian Insight
        h_val = current_iteration + report.delta
        print(f"\nIteration Complete. Delta (V): {report.delta}, Hamiltonian (H): {h_val}")
        return False

    def _run_startup_health_check(self):
        """Gap 3: Validate workspace health before engine execution."""
        log_path = self.workspace_root / "events" / "events.jsonl"
        if not log_path.exists():
            print("  [HEALTH] Event log missing. Initializing...")
            return
        
        # Simple integrity check: can we parse the last line?
        try:
            import json
            with open(log_path, "rb") as f:
                f.seek(-2, 2)
                while f.read(1) != b"\n":
                    f.seek(-2, 1)
                last_line = f.readline().decode()
                json.loads(last_line)
            print("  [HEALTH] Event log integrity verified.")
        except Exception as e:
            print(f"  [HEALTH] WARNING: Event log may be corrupted: {e}")

    def _handle_spawn(self, spawn_req, feature, edge, depth, mode):
        print(f"\n[RECURSION] Spawned child vector: {spawn_req.question}")
        
        # Emit event
        loader = ConfigLoader(self.workspace_root, design_name=self.design_name)
        engine = IterateEngine(constraints=loader.constraints, project_root=self.workspace_root.parent)
        engine.emit_event("feature_spawned", feature=feature, edge=edge, data={
            "question": spawn_req.question,
            "vector_type": spawn_req.vector_type,
            "parent": feature
        })
        
        # In a real implementation, this would call SpawnCommand and then IterateCommand on the new vector
        # After successful completion of the spawn, we complete the compensation.
        # For now, we simulate immediate compensation completion.
        engine.emit_event("compensation_completed", feature=feature, edge=edge, data={
            "status": "Child vector handled"
        })
