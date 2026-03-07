# Implements: REQ-SUPV-001
"""
Universal Guardrail Engine for Gemini Cloud.
Enforces hard invariants before construction begins.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class GuardrailResult:
    name: str
    passed: bool
    message: str

class TagValidator:
    """Enforces REQ key discipline in artifacts (REQ-EDGE-004)."""
    
    def validate(self, candidate: str) -> bool:
        if not candidate:
            return True # Empty is okay for new files
        return bool(re.search(r"(Implements|Validates).*?: REQ-", candidate))

class GuardrailEngine:
    """The safety controller of the SDLC (REQ-SUPV-001)."""
    
    def __init__(self, constraints: Dict[str, Any]):
        self.constraints = constraints or {}
        self.tag_validator = TagValidator()

    def validate_pre_flight(self, edge: str, context: Dict) -> List[GuardrailResult]:
        """Check invariants BEFORE the iterate loop starts."""
        results = []
        
        # Guardrail 1: Dependency Check
        if "design" in edge and not context.get("upstream_converged", True):
            results.append(GuardrailResult(
                name="upstream_dependency",
                passed=False,
                message="Cannot iterate on this edge until upstream asset is stable."
            ))

        # Guardrail 2: Security Policy
        if self.constraints.get("classification") == "confidential":
            if not context.get("security_scanner_enabled", False):
                results.append(GuardrailResult(
                    name="security_gate",
                    passed=False,
                    message="Confidential projects require mandatory security scanning."
                ))

        return results

    def validate_post_flight(self, edge: str, candidate: str) -> List[GuardrailResult]:
        """Check invariants AFTER construction (e.g., tagging)."""
        results = []
        
        # REQ-EDGE-004: Tagging Discipline
        if any(keyword in edge.lower() for keyword in ["code", "test", "design", "requirements"]):
            passed = self.tag_validator.validate(candidate)
            results.append(GuardrailResult(
                name="tagging_discipline",
                passed=passed,
                message="Artifact has mandatory REQ tags." if passed else "Artifact is missing mandatory 'Implements: REQ-*' or 'Validates: REQ-*' tag."
            ))
        
        return results
