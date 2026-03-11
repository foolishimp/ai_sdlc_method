# Implements: REQ-ITER-001, REQ-ITER-002, REQ-LIFE-008, REQ-TOOL-003, ADR-021
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
from gemini_cli.engine.models import Outcome

class IterateCommand:
    """Universal Iteration Agent command with Dual-Mode Dispatcher.
    Implements: REQ-TOOL-003 (Workflow Commands)
    """
    
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
        
        # 2. Configure Stateless Engine with Dynamic Routing (ADR-GG-002)
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
        
        asset_path = Path(asset)
        
        # 3. Load context
        fv_path = self.workspace_root / "features" / "active" / f"{feature}.yml"
        fv_data = {}
        if fv_path.exists():
            with open(fv_path, "r") as f:
                fv_data = yaml.safe_load(f) or {}

        # 4. Run Orchestrated Edge Traversal (Phase 2)
        records = engine.run_edge(
            edge=normalized_edge,
            feature_id=feature,
            asset_path=asset_path,
            context={
                "asset_name": asset,
                "edge": normalized_edge,
                "mode": mode,
                "feature_id": feature,
                "feature_vector": fv_data
            },
            mode=mode,
            construct=(mode != "interactive"),
            max_iterations=10
        )
        
        if not records:
            return False
            
        last_record = records[-1]
        
        # 5. Display Results of last iteration
        for res in last_record.report.functor_results:
            icon = "[PASS]" if res.outcome == Outcome.PASS else "[FAIL]"
            print(f"    {icon} {res.name}: {res.reasoning} (Delta: {res.delta})")
            
        for g in last_record.report.guardrail_results:
            icon = "[SAFE]" if g.passed else "[WARN]"
            print(f"    {icon} Guardrail {g.name}: {g.message}")

        if last_record.converged:
            print(f"\nSuccess! {normalized_edge} converged after {len(records)} iterations.")
            return True
        
        # Check if blocked by spawn
        from gemini_cli.engine.fd_spawn import load_events
        events = load_events(self.workspace_root)
        relevant_spawn = next((e for e in reversed(events) if e.get("event_type") == "spawn_created" and e.get("feature") == feature and e.get("edge") == normalized_edge), None)
        if relevant_spawn:
            print(f"\n[RECURSION] Edge blocked by spawned child vector.")
            return True

        print(f"\nIteration set complete. Final Delta (V): {last_record.delta}, Hamiltonian (H): {last_record.hamiltonian}")
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
