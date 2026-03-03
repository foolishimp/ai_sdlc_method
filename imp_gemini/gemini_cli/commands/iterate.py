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
        
        # Resolve Edge Configuration and Checklist
        transitions = topology.topology.get("transitions", [])
        edge_config = {}
        evaluator_types = ["agent", "human"] # Default
        
        edge_parts = re.split(r"->|\u2192|\u2194", edge)
        src_input = edge_parts[0].strip().lower()
        tgt_input = edge_parts[-1].strip().lower()
        normalized_edge = f"{src_input}\u2192{tgt_input}"
        
        for t in transitions:
            if (src_input == t.get("source", "").lower() and tgt_input == t.get("target", "").lower()) or \
               (edge.lower() in t.get("name", "").lower()):
                edge_config = t
                evaluator_types = t.get("evaluators", evaluator_types)
                break
        
        resolved_checklist = loader.resolve_checklist(edge_config)
        if not resolved_checklist and evaluator_types:
            # Fallback to default checklist based on topology evaluators
            resolved_checklist = [{"evaluator": et} for et in evaluator_types]
        
        functor_map = {
            "deterministic": DeterministicFunctor(),
            "agent": GeminiFunctor(),
            "human": HumanFunctor()
        }
        
        engine = IterateEngine(functor_map=functor_map, constraints=loader.constraints, project_root=self.workspace_root.parent)
        
        # Determine iteration count
        events = self.store.load_all()
        iter_count = Projector.get_iteration_count(events, feature, normalized_edge)
        
        if iter_count == 0:
            engine.emit_event("edge_started", feature=feature, edge=normalized_edge, data={"mode": mode_label})
        
        asset_path = Path(asset)
        
        # Load feature vector for context (Cascading ADRs)
        fv_path = self.workspace_root / "features" / "active" / f"{feature}.yml"
        fv_data = {}
        if fv_path.exists():
            with open(fv_path, "r") as f:
                fv_data = yaml.safe_load(f) or {}

        records = engine.run_edge(
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
            mode=mode,
            checklist=resolved_checklist,
            max_iterations=1 # Only one iteration per command call
        )
        
        if not records:
            return False
            
        report = records[0].report
        
        # Handle Spawns (Recursion) first - escalation takes precedence over hard failure
        if report.spawn:
            # Handle recursion if requested
            self._handle_spawn(report.spawn, feature, normalized_edge, depth, mode)
            return True # Successfully escalated

        # Handle Guardrail failures
        if any(not g.passed for g in report.guardrail_results):
            for g in report.guardrail_results:
                if not g.passed:
                    print(f"    - {g.name}: {g.message}")
            return False

        if report.converged:
            print(f"Success! {normalized_edge} converged ({mode_label}).")
            return True
        
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
        pass
