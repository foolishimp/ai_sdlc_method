# Implements: REQ-F-RUNTIME-001
"""Typed outcome algebra for the dispatch path.

Introduces explicit sum types that replace exception-as-control-flow and
sentinel patterns in edge_runner.py and fp_functor.py.

F_D outcomes:
    FdPassed   — evaluator ran; all checks pass (delta=0)
    FdFailed   — evaluator ran; checks failed (delta>0)
    FdError    — evaluator infrastructure broken (not a domain delta)

F_P outcomes:
    FpSkipped  — MCP unavailable; F_D-only mode (ADR-019, not an error)
    FpPending  — manifest written; awaiting actor fold-back result
    FpReturned — actor completed; fold-back result available
    FpFailed   — actor invocation failed; observable failure

IntentEvent:
    Typed projection of a raw intent_raised event dict.
    Constructed at intake boundary in intent_observer.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# ── F_D outcome algebra ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FdPassed:
    """Evaluator ran; all required checks pass."""

    delta: int = 0
    checks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FdFailed:
    """Evaluator ran; required checks failed. delta > 0."""

    delta: int
    failures: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FdError:
    """Evaluator infrastructure broken — NOT a feature delta.

    Callers must NOT increment delta or schedule another iteration on this
    result. The feature's state is unknown; the evaluator is the problem.
    """

    error: str
    traceback: str = ""


FdOutcome = FdPassed | FdFailed | FdError


# ── F_P outcome algebra ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FpSkipped:
    """MCP unavailable — F_D-only mode (ADR-019). Not an error."""

    reason: str = "MCP unavailable"


@dataclass(frozen=True)
class FpPending:
    """Manifest written; waiting for actor fold-back result."""

    manifest_path: Path


@dataclass(frozen=True)
class FpReturned:
    """Actor completed; fold-back result available."""

    result: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FpFailed:
    """Actor invocation failed — observable failure, not a silent skip."""

    error: str
    traceback: str = ""


FpOutcome = FpSkipped | FpPending | FpReturned | FpFailed


# ── Intent event typed boundary ────────────────────────────────────────────────


@dataclass(frozen=True)
class IntentEvent:
    """Typed projection of a raw intent_raised event dict.

    Constructed at the intake boundary inside intent_observer.py.
    The internal dispatch routing never passes raw dicts — always IntentEvent.
    """

    intent_id: str
    feature_id: str
    signal_source: str
    timestamp: str
    raw: dict = field(default_factory=dict, compare=False, hash=False)

    @classmethod
    def from_dict(cls, event: dict) -> "IntentEvent":
        """Project raw event dict to IntentEvent at intake boundary.

        Handles both flat format (fields at top level) and nested format
        (fields under a 'data' sub-dict).
        """
        data = event.get("data", {}) or {}

        # Resolve feature_id from several possible locations
        affected = data.get("affected_features") or event.get("affected_features") or []
        feature_id = (
            (affected[0] if isinstance(affected, list) and affected else "")
            or data.get("feature", "")
            or event.get("feature", "")
        )

        intent_id = (
            data.get("intent_id", "")
            or event.get("intent_id", "")
        )
        signal_source = (
            data.get("signal_source", "")
            or event.get("signal_source", "")
        )
        timestamp = event.get("timestamp", "")

        return cls(
            intent_id=intent_id,
            feature_id=feature_id,
            signal_source=signal_source,
            timestamp=timestamp,
            raw=event,
        )
