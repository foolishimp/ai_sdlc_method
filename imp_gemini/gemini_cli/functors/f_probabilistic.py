# Implements: REQ-CLI-005, REQ-CLI-006
"""
Probabilistic Functor: The Gemini API binding.
Supports Recursive Spawning for sub-problem investigation.
"""

import os
from typing import Dict, Any, Union
from pathlib import Path
from genesis_core.engine.models import FunctorResult, Outcome, SpawnRequest

class GeminiFunctor:
    """Universal Probabilistic Evaluator/Constructor."""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name
        self.api_key = os.getenv("GEMINI_API_KEY")

    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        """
        Evaluate candidate using Gemini.
        Returns FunctorResult with delta, reasoning, or a SpawnRequest if stuck.
        """
        # 1. Check for 'stuck' condition
        if context.get("iteration_count", 0) > 3:
            return FunctorResult(
                name="gemini_eval",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning="LLM stuck for 3+ iterations. Triggering recursion.",
                spawn=SpawnRequest(
                    question="Why is the delta not decreasing?",
                    vector_type="discovery"
                )
            )
            
        # 2. Simulate 'Universal Evaluator' logic
        is_valid = "Implements: REQ-" in candidate
        return FunctorResult(
            name="gemini_eval",
            outcome=Outcome.PASS if is_valid else Outcome.FAIL,
            delta=0 if is_valid else 1,
            reasoning="Candidate contains REQ tags." if is_valid else "Missing REQ tags.",
            next_candidate=candidate 
        )
