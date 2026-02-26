# Implements: REQ-SUPV-001
"""
Universal Guardrail Engine.
Enforces hard invariants before construction begins.
"""

from typing import Dict, Any, List
from pathlib import Path
from .models import GuardrailResult

class GuardrailEngine:
    """The safety controller of the SDLC."""
    
    def __init__(self, constraints: Dict[str, Any]):
        self.constraints = constraints

    def validate_pre_flight(self, edge: str, context: Dict) -> List[GuardrailResult]:
        """Check invariants BEFORE the iterate loop starts."""
        results = []
        
        # Guardrail 1: Dependency Check
        # Example: Cannot iterate on 'code' if 'design' is not converged.
        if "design" in edge and not context.get("upstream_converged", True):
            results.append(GuardrailResult(
                name="upstream_dependency",
                passed=False,
                message="Cannot iterate on this edge until upstream asset is stable."
            ))

        # Guardrail 2: Security Policy
        # Example: If project is 'confidential', certain tools are mandatory.
        if self.constraints.get("classification") == "confidential":
            if not context.get("security_scanner_enabled", False):
                results.append(GuardrailResult(
                    name="security_gate",
                    passed=False,
                    message="Confidential projects require mandatory security scanning."
                ))

        return results
