# Implements: REQ-CLI-005
"""
Deterministic Functor: The Subprocess Binding.
Executes shells commands, test runners, and linters.
"""

import subprocess
from typing import Dict, Any

class DeterministicFunctor:
    """Zero-ambiguity evaluator (pytest, ruff, etc.)."""
    
    def evaluate(self, candidate: str, context: Dict) -> Dict[str, Any]:
        command = context.get("command")
        if not command:
            return {"delta": 0, "reasoning": "No deterministic command provided."}
            
        try:
            # Run the command (e.g., pytest)
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=context.get("cwd")
            )
            
            success = result.returncode == 0
            return {
                "delta": 0 if success else 1,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "reasoning": "Check passed." if success else "Command failed."
            }
        except Exception as e:
            return {"delta": 1, "reasoning": f"Execution error: {str(e)}"}
