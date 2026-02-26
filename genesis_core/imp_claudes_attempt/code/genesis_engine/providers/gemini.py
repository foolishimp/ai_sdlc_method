# Implements: GENESIS_ENGINE_SPEC §6.2 (F_P Binding Point)
"""Gemini provider stub — F_P evaluation via Gemini CLI.

This is a placeholder. A real implementation would use the Gemini CLI
or API to evaluate agent checks. The interface is identical to Claude's.
"""

from ..models import CheckOutcome, CheckResult, ResolvedCheck
from .base import FPProvider


class GeminiProvider(FPProvider):
    """F_P provider stub for Gemini."""

    def __init__(self, model: str = "gemini-2.5-pro", **kwargs):
        self._model = model

    @property
    def name(self) -> str:
        return "gemini"

    def run_check(
        self,
        check: ResolvedCheck,
        asset_content: str,
        context: str = "",
        timeout: int = 120,
    ) -> CheckResult:
        """Stub — returns SKIP until Gemini CLI integration is implemented."""
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.SKIP,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Gemini provider not yet implemented (model: {self._model})",
        )
