# Implements: REQ-CLI-005, REQ-CLI-006
"""
Probabilistic Functor: The Sub-Agent Binding.
Hands control back to the Gemini CLI session for complex work.
"""
import sys
import traceback
from typing import Dict, Any, Union
from gemini_cli.engine.models import FunctorResult, Outcome, SpawnRequest

class GeminiFunctor:
    """Functor that delegates work to the interactive Gemini CLI (Sub-Agent)."""
    
    def __init__(self, model_name: str = "gemini-interactive"):
        self.model_name = model_name

    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        """
        Structured delegation to the user (the Sub-Agent).
        """
        try:
            if context is None:
                context = {}
                
            iteration_count = context.get("iteration_count", 0)
            
            # REQ-CLI-006: Automatic recursion detection for stuck features
            if iteration_count >= 3:
                spawn = SpawnRequest(
                    question=f"Feature stuck after {iteration_count} iterations. Investigate root cause.",
                    vector_type="discovery"
                )
                return FunctorResult(
                    name="sub_agent_eval",
                    outcome=Outcome.FAIL,
                    delta=1,
                    reasoning=f"Triggering recursion (iteration {iteration_count}). Stuck feature detected.",
                    spawn=spawn
                )

            print("\n" + "═"*60)
            print(" SUB-AGENT ITERATION REQUIRED")
            print("═"*60)
            print(f"Goal: {context.get('edge', 'General Construction')}")
            print(f"Asset: {context.get('asset_name', 'Unknown')}")
            
            # Display linked ADRs (Cascading context)
            fv = context.get("feature_vector", {})
            adrs = fv.get("context", {}).get("adrs", [])
            if adrs:
                print(f"Linked ADRs: {', '.join(adrs)}")
                
                # The full constraints are in context["constraints"] if passed from engine
                all_adr_content = context.get("constraints", {}).get("context", {}).get("adrs", {})
                if not all_adr_content:
                    all_adr_content = context.get("adrs", {})
                
                if all_adr_content:
                    print("--- Relevant Architectural Context ---")
                    for adr_id in adrs[:3]: # Show first 3 for brevity
                        content = all_adr_content.get(adr_id, "")
                        if content:
                            # Show first 2 non-empty lines of each ADR
                            lines = [l for l in content.splitlines() if l.strip()]
                            summary = "\n".join(lines[:2])
                            print(f"[{adr_id}] {summary}\n...")
            
            print("-" * 20)
            print("TASK: Please evaluate/construct the candidate against the requirements.")
            print("Use your tools (read_file, run_shell_command) to validate.")
            print("-" * 20)
            
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
        except Exception as e:
            print(f"  [ERROR] in GeminiFunctor: {str(e)}")
            traceback.print_exc()
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.ERROR,
                delta=1,
                reasoning=f"Internal error: {str(e)}"
            )
