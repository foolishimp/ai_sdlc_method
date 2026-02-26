
import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from genesis_core.engine.state import EventStore

class InitCommand:
    """Scaffolds a new AI SDLC workspace."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.store = EventStore(workspace_root)

    def run(self, project_name: str, impl: str = "gemini"):
        # 1. Create Directory Structure
        dirs = [
            "specification",
            f"imp_{impl}/design/adrs",
            f"imp_{impl}/code",
            f"imp_{impl}/tests",
            ".ai-workspace/graph/edges",
            f".ai-workspace/{impl}_genesis/context/data_models",
            f".ai-workspace/{impl}_genesis/context/templates",
            f".ai-workspace/{impl}_genesis/context/policy",
            ".ai-workspace/features/active",
            ".ai-workspace/features/completed",
            ".ai-workspace/events",
            ".ai-workspace/tasks/active",
            ".ai-workspace/snapshots",
        ]
        
        for d in dirs:
            (self.workspace_root.parent / d).mkdir(parents=True, exist_ok=True)

        # 2. Emit Project Initialized Event
        self.store.emit(
            "project_initialized", 
            project=project_name,
            data={
                "impl": impl,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        print(f"Project {project_name} initialized at {self.workspace_root}")
