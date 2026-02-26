import os
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime, timezone
from gemini_cli.engine.state import EventStore

class InitCommand:
    """Scaffolds a new AI SDLC workspace."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)

    def run(self, project_name: str, impl: str = "gemini"):
        project_root = self.workspace_root.parent
        config_src = Path(__file__).parent.parent / "config"
        
        # 1. Create Directory Structure
        dirs = [
            "specification",
            f"imp_{impl}/design/adrs",
            f"imp_{impl}/code",
            f"imp_{impl}/tests",
            ".ai-workspace/graph/edges",
            f".ai-workspace/{impl}_genesis/adrs",
            f".ai-workspace/{impl}_genesis/data_models",
            f".ai-workspace/{impl}_genesis/templates",
            f".ai-workspace/{impl}_genesis/policy",
            f".ai-workspace/{impl}_genesis/standards",
            ".ai-workspace/features/active",
            ".ai-workspace/features/completed",
            ".ai-workspace/events",
            ".ai-workspace/tasks/active",
            ".ai-workspace/snapshots",
        ]
        
        for d in dirs:
            (project_root / d).mkdir(parents=True, exist_ok=True)

        # 2. Copy Graph Topology Configuration (GAP-042)
        if config_src.exists():
            # Copy graph_topology.yml
            shutil.copy2(config_src / "graph_topology.yml", project_root / ".ai-workspace" / "graph" / "graph_topology.yml")
            # Copy edge_params
            for edge_cfg in (config_src / "edge_params").glob("*.yml"):
                shutil.copy2(edge_cfg, project_root / ".ai-workspace" / "graph" / "edges" / edge_cfg.name)
            # Copy project_constraints template
            shutil.copy2(config_src / "project_constraints_template.yml", project_root / ".ai-workspace" / f"{impl}_genesis" / "project_constraints.yml")

        # 3. Create STATUS.md (GAP-025)
        status_file = project_root / ".ai-workspace" / "STATUS.md"
        status_content = f"""# Project Status: {project_name}

Generated: {datetime.now(timezone.utc).isoformat()}

## Feature Build Schedule

```mermaid
gantt
    title Feature Build Schedule
    dateFormat YYYY-MM-DD HH:mm
    axisFormat %m-%d %H:%M
```

## Process Telemetry
- Total features: 0
- Total events: 1

## Self-Reflection
- Project initialized.
"""
        status_file.write_text(status_content)

        # 4. Emit Project Initialized Event
        self.store.emit(
            "project_initialized", 
            project=project_name,
            data={
                "impl": impl,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        print(f"Project {project_name} initialized at {project_root}")
