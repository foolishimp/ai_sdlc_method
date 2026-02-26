# Implements: REQ-CLI-005, REQ-CLI-006
"""
Probabilistic Functor: The Sub-Agent Binding.
Hands control back to the Gemini CLI session for complex work.
"""

from typing import Dict, Any, Union
from ..engine.models import FunctorResult, Outcome, SpawnRequest

class GeminiFunctor:
    """Functor that delegates work to the interactive Gemini CLI (Sub-Agent)."""
    
    def __init__(self, model_name: str = "gemini-interactive"):
        self.model_name = model_name

    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        """
        Structured delegation to the user (the Sub-Agent).
        """
        iteration_count = context.get("iteration_count", 0)
        
        # REQ-CLI-006: Automatic recursion detection for stuck features
        if iteration_count >= 3:
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning=f"Triggering recursion (iteration {iteration_count}). Stuck feature detected.",
                spawn=SpawnRequest(
                    question=f"Feature stuck after {iteration_count} iterations. Investigate root cause.",
                    vector_type="discovery"
                )
            )

        print("\n" + "═"*60)
        print(" SUB-AGENT ITERATION REQUIRED")
        print("═"*60)
        print(f"Goal: {context.get('edge', 'General Construction')}")
        print(f"Asset: {context.get('asset_name', 'Unknown')}")
        print("-" * 20)
        print("TASK: Please evaluate/construct the candidate against the requirements.")
        print("Use your tools (read_file, run_shell_command) to validate.")
        print("-" * 20)
        
        # In a real sub-agent flow, we might use ask_user here.
        # For this CLI MVP, we'll use standard input to get the signal.
        
        choice = input("Convergence? (y = Pass / n = Fail / s = Spawn Recursion): ").lower().strip()
        
        if choice == 'y':
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.PASS,
                delta=0,
                reasoning="Sub-Agent confirmed convergence."
            )
        elif choice == 's':
            reason = input("Why is recursion required? ")
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning=f"Sub-Agent requested recursion: {reason}",
                spawn=SpawnRequest(question=reason, vector_type="discovery")
            )
        else:
            feedback = input("Provide feedback for the next iteration: ")
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning=feedback
            )
