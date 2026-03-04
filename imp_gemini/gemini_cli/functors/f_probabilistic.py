# Implements: REQ-CLI-005, REQ-CLI-006
"""
Probabilistic Functor: The Sub-Agent Binding.
Hands control back to the Gemini CLI session for complex work.
"""
import sys
import traceback
import re
from typing import Dict, Any, Union
from gemini_cli.engine.models import FunctorResult, Outcome, SpawnRequest

class GeminiFunctor:
    """Functor that delegates work to the interactive Gemini CLI (Sub-Agent)."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name

    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        """
        Structured delegation to the agent or user.
        """
        tracer = None
        span = None
        try:
            from opentelemetry import trace
            tracer = trace.get_tracer(__name__)
            # Inner Loop Span (OpenInference pattern)
            span_context = tracer.start_as_current_span(
                "GeminiFunctor:Evaluate",
                attributes={
                    "llm.model_name": self.model_name,
                    "sdlc.feature_id": context.get("feature_id", "unknown"),
                    "sdlc.edge_id": context.get("edge", "unknown"),
                    "input.value": candidate[:1000] # Truncate for telemetry
                }
            )
            span = span_context.__enter__()
        except ImportError:
            pass

        try:
            if context is None:
                context = {}
                
            iteration_count = context.get("iteration_count", 0)
            mode = context.get("mode", "interactive")
            
            # REQ-CLI-006: Automatic recursion detection for stuck features
            if iteration_count >= 3:
                spawn = SpawnRequest(
                    question=f"Feature stuck after {iteration_count} iterations. Investigate root cause.",
                    vector_type="discovery"
                )
                res = FunctorResult(
                    name="sub_agent_eval",
                    outcome=Outcome.FAIL,
                    delta=1,
                    reasoning=f"Triggering RECURSION (iteration {iteration_count}). Stuck feature detected.",
                    spawn=spawn
                )
                if span: 
                    span.set_attribute("output.value", res.reasoning)
                    span.set_attribute("sdlc.status", "stuck_recursion")
                return res

            if mode == "headless":
                res = self._evaluate_headless(candidate, context)
            else:
                res = self._evaluate_interactive(candidate, context)

            if span:
                span.set_attribute("output.value", res.reasoning)
                span.set_attribute("sdlc.outcome", res.outcome.name)
                span.set_attribute("sdlc.delta", res.delta)
            
            return res

        except Exception as e:
            error_msg = f"Internal error: {str(e)}"
            if span:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
            
            print(f"  [ERROR] in GeminiFunctor: {str(e)}")
            traceback.print_exc()
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.ERROR,
                delta=1,
                reasoning=error_msg
            )
        finally:
            if span:
                span_context.__exit__(None, None, None)

    def _evaluate_headless(self, candidate: str, context: Dict) -> FunctorResult:
        """Automated heuristic evaluation for headless mode."""
        feature_id = context.get("feature_id", "unknown")
        edge = context.get("edge", "")
        
        # Simple heuristic: if it's 'code' edge, check for REQ tags
        if "code" in edge:
            if re.search(rf"Implements:\s*{feature_id}", candidate) or re.search(rf"REQ-", candidate):
                return FunctorResult(
                    name="sub_agent_eval",
                    outcome=Outcome.PASS,
                    delta=0,
                    reasoning=f"Headless: Found traceability tags for {feature_id}."
                )
            else:
                return FunctorResult(
                    name="sub_agent_eval",
                    outcome=Outcome.FAIL,
                    delta=1,
                    reasoning=f"Headless: Missing traceability tags for {feature_id} in code."
                )
        
        # For other edges, if candidate is not empty, assume progress for now
        if candidate.strip():
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.PASS,
                delta=0,
                reasoning="Headless: Candidate present and non-empty."
            )
        else:
            return FunctorResult(
                name="sub_agent_eval",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning="Headless: Candidate is empty."
            )

    def _evaluate_interactive(self, candidate: str, context: Dict) -> FunctorResult:
        """Interactive evaluation via user input."""
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
            
            all_adr_content = context.get("constraints", {}).get("context", {}).get("adrs", {})
            if not all_adr_content:
                all_adr_content = context.get("adrs", {})
            
            if all_adr_content:
                print("--- Relevant Architectural Context ---")
                for adr_id in adrs[:3]:
                    content = all_adr_content.get(adr_id, "")
                    if content:
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
