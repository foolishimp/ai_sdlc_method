# Observability Spike: AI SDLC + Arize Phoenix (Lineage)
# Implements: ADR-S-014 (OTLP-Phoenix Standard)
# 
# This script scaffolds a temporary project, starts the Sensory OTLP Relay,
# and runs a full iteration loop across 4 edges with lineage pathing. 

import os
import time
import json
import shutil
import pathlib
import threading
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# --- Import methodology engine ---
from gemini_cli.engine.sensory import SensoryService
from gemini_cli.commands.iterate import IterateCommand
from gemini_cli.engine.state import EventStore

def setup_spike_project(tmp_path: Path):
    """Scaffolds a tiny project for the spike."""
    ws = tmp_path / ".ai-workspace"
    config_src = Path("imp_gemini/gemini_cli/config")
    
    # 1. Directories
    dirs = ["graph/edges", "profiles", "features/active", "events", "gemini_genesis", "spec"]
    for d in dirs:
        (ws / d).mkdir(parents=True, exist_ok=True)
        
    # 2. Configs
    shutil.copy2(config_src / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(config_src / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in (config_src / "edge_params").glob("*.yml"):
        shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in (config_src / "profiles").glob("*.yml"):
        shutil.copy2(yml, ws / "profiles" / yml.name)
        
    # 3. Project specific context
    (ws / "spec" / "INTENT.md").write_text("# Intent\nBuild a temperature converter.")
    (ws / "gemini_genesis" / "project_constraints.yml").write_text(textwrap.dedent("""
        project:
          name: "obs-spike-project"
        engineering:
          languages: ["python"]
          testing_frameworks: ["pytest"]
    """))
    
    # 4. Feature Vector
    with open(ws / "features" / "active" / "REQ-F-LINEAGE-SPIKE.yml", "w") as f:
        f.write("feature: REQ-F-LINEAGE-SPIKE\nstatus: pending\ntrajectory: {}")
        
    # 5. Initialization event
    store = EventStore(ws)
    store.emit("project_initialized", project="obs-spike-project")
    
    return tmp_path

def run_spike():
    # Setup temp dir
    spike_dir = Path("/tmp/sdlc-obs-spike-lineage")
    if spike_dir.exists():
        shutil.rmtree(spike_dir)
    spike_dir.mkdir(parents=True)
    
    print(f"\n[SPIKE] Scaffolding project at {spike_dir}")
    setup_spike_project(spike_dir)
    
    # Start Sensory Service (including OTLP Relay)
    print("[SPIKE] Starting Sensory Service + OTLP Relay...")
    sensory = SensoryService(spike_dir / ".ai-workspace")
    sensory_thread = threading.Thread(target=sensory.start_background_service, kwargs={"interval": 5}, daemon=True)
    sensory_thread.start()
    
    time.sleep(2) # Give relay time to start
    
    # Run full iteration loop
    print("[SPIKE] Running Iterate Command (headless mode)...")
    command = IterateCommand(spike_dir / ".ai-workspace")
    
    # Simulate a full traversal of the standard profile
    edges = [
        "intent\u2192requirements",
        "requirements\u2192design",
        "design\u2192code",
        "code\u2194unit_tests"
    ]
    
    for edge in edges:
        asset_name = "src/converter.py" if "code" in edge else "spec/requirements.md"
        print(f"  > Iterating edge: {edge}")
        command.run(feature="REQ-F-LINEAGE-SPIKE", edge=edge, asset=asset_name, mode="headless")
        time.sleep(1) # Pace for visibility

    print("\n" + "="*60)
    print(" SPIKE COMPLETE (Lineage Path enabled)")
    print("="*60)
    print(f"Project Log: {spike_dir / '.ai-workspace' / 'events' / 'events.jsonl'}")
    print("\n1. Start Phoenix: python -m phoenix.server.main serve")
    print("2. Open UI: http://localhost:6006")
    print("3. Filter by 'sdlc.feature_id == REQ-F-LINEAGE-SPIKE' to see the trace tree.")
    print("="*60)
    
    # Keep alive for a moment to let the relay finish tailing
    print("\nWaiting 10s for OTLP Relay to finish flushing...")
    time.sleep(10)
    sensory.stop()

if __name__ == "__main__":
    run_spike()
