import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add imp_gemini to sys.path
sys.path.append(str(Path.cwd() / "imp_gemini"))

from gemini_cli.engine.prefect import run_sdlc_workflow

@dataclass
class AgentResult:
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metrics: Dict[str, Any] = None
    messages: Any = None
    raw_output: str = ""

class MockAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def process(self, context: Dict[str, Any]) -> AgentResult:
        print(f"  [MOCK] Agent processing edge: {context.get('edge')}")
        time.sleep(2) # Simulate work
        return AgentResult(
            success=True,
            data={"delta": 0, "message": "Mock agent converged successfully."},
            metrics={"tokens": 100, "latency_ms": 2000}
        )

def main():
    edge = "design\u2194code"
    feature_id = "REQ-F-MOCK-001"
    asset_path = Path.cwd() / "imp_gemini" / "tests" / "mock_asset.txt"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_text("Mock Asset Content")
    
    context = {
        "project": "imp_gemini",
        "workspace_root": str(Path.cwd() / "imp_gemini" / ".ai-workspace")
    }
    
    config = {"model": "mock-v1"}
    
    print(f"  [TEST] Starting Prefect workflow for {feature_id}...")
    
    # Run the Prefect flow
    # Note: We pass the class itself for this mock test
    result = run_sdlc_workflow(
        edge=edge,
        feature_id=feature_id,
        asset_path=asset_path,
        context=context,
        agent_class=MockAgent,
        config=config
    )
    
    print(f"\n  [TEST] Workflow finished with status: {result.get('status')}")
    print(f"  [TEST] Workflow Run ID: {result.get('workflow_id')}")
    print(f"  [TEST] Data: {result.get('result_data')}")

if __name__ == "__main__":
    from typing import Optional
    main()
