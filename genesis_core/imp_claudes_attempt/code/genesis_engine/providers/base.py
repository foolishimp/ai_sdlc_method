# Implements: GENESIS_ENGINE_SPEC §6.2 (F_P Binding Point)
"""Abstract base for F_P providers — the pluggable LLM interface.

Every provider must implement `run_check()`. The engine calls it for
agent-type checks. Everything else (dispatch, delta, emission) is F_D.
"""

from abc import ABC, abstractmethod

from ..models import CheckResult, ResolvedCheck


class FPProvider(ABC):
    """Abstract F_P provider — one method, one contract."""

    @abstractmethod
    def run_check(
        self,
        check: ResolvedCheck,
        asset_content: str,
        context: str = "",
        timeout: int = 120,
    ) -> CheckResult:
        """Evaluate a single agent check using an LLM.

        The provider is responsible for:
        1. Building a prompt from the check criterion + asset content
        2. Calling its LLM (Claude, Gemini, Codex, local, etc.)
        3. Parsing the response into a CheckResult

        The provider must NOT:
        - Emit events (that's F_D's job)
        - Modify files on disk
        - Make routing decisions

        Args:
            check: The resolved check to evaluate.
            asset_content: Content of the asset being evaluated.
            context: Additional context string.
            timeout: Maximum seconds for the LLM call.

        Returns:
            CheckResult with outcome, message, and diagnostics.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'claude', 'gemini')."""
        ...
