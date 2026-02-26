# Implements: REQ-CLI-005
"""
Deterministic Functor: The Subprocess Binding.
Executes shell commands, test runners, and linters.
"""

import subprocess
from typing import Dict, Any
from gemini_cli.engine.models import FunctorResult, Outcome

class DeterministicFunctor:
    """Zero-ambiguity evaluator (pytest, sbt, ruff, etc.)."""
    
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        command = context.get("command")
        if not command:
            return FunctorResult(
                name="deterministic_shell",
                outcome=Outcome.SKIP,
                delta=0,
                reasoning="No deterministic command provided."
            )
            
        try:
            print(f"  [RUNNING] {command}...")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=context.get("cwd")
            )
            
            success = result.returncode == 0
            # Capture the first few lines of error for reasoning
            short_err = result.stderr[:500] if result.stderr else (result.stdout[:500] if not success else "")
            
            return FunctorResult(
                name="deterministic_shell",
                outcome=Outcome.PASS if success else Outcome.FAIL,
                delta=0 if success else 1,
                reasoning="Check passed." if success else f"Command failed: {short_err}",
                metadata={"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
            )
        except Exception as e:
            return FunctorResult(
                name="deterministic_shell",
                outcome=Outcome.ERROR,
                delta=1,
                reasoning=f"Execution error: {str(e)}"
            )
