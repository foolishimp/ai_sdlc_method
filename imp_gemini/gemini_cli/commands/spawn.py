
import yaml
from pathlib import Path
from gemini_cli.engine.state import EventStore

class SpawnCommand:
    """Creates a new feature vector (Feature, Discovery, Spike, etc.)."""
    
    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.store = EventStore(workspace_root)

    def run(self, feature_id: str, intent_id: str, vector_type: str = "feature", parent: str = None):
        fv_path = self.workspace_root / "features" / "active" / f"{feature_id}.yml"
        
        # Resolve ADRs from context
        from gemini_cli.engine.config_loader import ConfigLoader
        loader = ConfigLoader(self.workspace_root, design_name=self.design_name)
        adr_keys = list(loader.constraints.get("context", {}).get("adrs", {}).keys())
        
        # 1. Create Feature Vector YAML
        data = {
            "feature": feature_id,
            "intent": intent_id,
            "vector_type": vector_type,
            "status": "pending",
            "parent": parent,
            "context": {
                "adrs": sorted(adr_keys)
            },
            "trajectory": {
                "intent": {"status": "converged"}
            }
        }
        
        with open(fv_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)

        # 2. Emit Event
        self.store.emit(
            "feature_spawned",
            project="unknown", # Resolved by Store
            feature=feature_id,
            data={
                "vector_type": vector_type,
                "parent": parent,
                "intent": intent_id,
                "context": data["context"]
            }
        )
        
        print(f"Spawned {vector_type} vector: {feature_id} (Linked ADRs: {len(adr_keys)})")
