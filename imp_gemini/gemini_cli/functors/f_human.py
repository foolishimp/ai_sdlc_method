# Implements: REQ-CLI-005
"""
Human Functor: The Judgment Binding.
Prompts the developer for approval or refinement.
"""

from typing import Dict, Any
from genesis_core.engine.models import FunctorResult, Outcome

class HumanFunctor:
    """Judgment-based evaluator (Ask the user)."""
    
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        print("\n" + "="*40)
        print("HUMAN EVALUATION REQUIRED")
        print("="*40)
        print(f"Asset: {context.get('asset_name', 'Unknown')}")
        print("-" * 20)
        print(candidate[:500] + "..." if len(candidate) > 500 else candidate)
        print("-" * 20)
        
        prompt = context.get("prompt", "Does this candidate satisfy the requirements?")
        choice = input(f"{prompt} (y/n/r): ").lower().strip()
        
        if choice == 'y':
            return FunctorResult(
                name="human_judgment",
                outcome=Outcome.PASS,
                delta=0,
                reasoning="Human approved."
            )
        elif choice == 'r':
            feedback = input("Provide refinement guidance: ")
            return FunctorResult(
                name="human_judgment",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning=feedback
            )
        else:
            return FunctorResult(
                name="human_judgment",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning="Human rejected."
            )
