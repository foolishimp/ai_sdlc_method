import sys
from pathlib import Path
from typing import Dict, Any

# Add imp_gemini to sys.path
sys.path.append(str(Path.cwd() / "imp_gemini"))

from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.engine.models import FunctorResult, Outcome

class AgentFunctor:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config
        
    def process(self, context: Dict[str, Any]):
        print(f"  [ENGINE-TEST] Prefect-managed agent running for edge: {context.get('edge')}")
        return type('obj', (object,), {
            'success': True,
            'data': {'delta': 0},
            'error': None,
            'metrics': {'tokens': 50},
            'messages': None,
            'raw_output': ""
        })

def main():
    # Setup Engine
    functor_map = {"agent": AgentFunctor()}
    engine = IterateEngine(functor_map=functor_map, project_root=Path.cwd() / "imp_gemini")
    
    edge = "design\u2194code"
    feature_id = "REQ-F-PREFECT-ENGINE-001"
    asset_path = Path.cwd() / "imp_gemini" / "tests" / "engine_mock_asset.txt"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_text("# Implements: REQ-F-PREFECT-ENGINE-001\nEngine Mock Asset Content")
    
    context = {
        "project": "imp_gemini",
        "feature_id": feature_id,
        "edge": edge,
        "workspace_root": str(Path.cwd() / "imp_gemini" / ".ai-workspace")
    }
    
    print(f"  [TEST] Running IterateEngine.iterate_edge in PREFECT mode...")
    
    # Run the engine test with multiple checks
    checklist = [
        {"evaluator": "deterministic", "name": "lint"},
        {"evaluator": "agent", "name": "code_quality"}
    ]
    
    record = engine.iterate_edge(
        edge=edge,
        feature_id=feature_id,
        asset_path=asset_path,
        context=context,
        mode="prefect",
        checklist=checklist
    )
    
    print(f"\n  [TEST] Engine Record Result:")
    print(f"  [TEST] Converged: {record.report.converged}")
    print(f"  [TEST] Delta: {record.report.delta}")
    
    if record.report.converged:
        print("  [TEST] SUCCESS: IterateEngine successfully delegated to Prefect.")
    else:
        print("  [TEST] FAILED: IterateEngine failed to converge via Prefect.")
        if hasattr(record.report, 'functor_results') and record.report.functor_results:
             print(f"  [TEST] Results: {record.report.functor_results}")
        if hasattr(record.report, 'guardrail_results') and record.report.guardrail_results:
             print(f"  [TEST] Guardrails: {record.report.guardrail_results}")
        else:
             print("  [TEST] No functor results returned.")

if __name__ == "__main__":
    main()
