# Implements: REQ-F-DISPATCH-001, REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Durable intent observer loop for dispatching pending intents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable

from .commands import gen_dispatch_intents


@dataclass(frozen=True)
class IntentObserverResult:
    """Summary of one observer session over the event log."""

    actor: str
    polls: int
    idle_polls: int
    dispatched_count: int
    dispatches: list[dict[str, Any]]
    stopped_reason: str


def run_intent_observer(
    project_root: Path,
    *,
    actor: str = "intent-observer",
    poll_interval_seconds: float = 5.0,
    max_polls: int | None = None,
    idle_polls_before_stop: int | None = None,
    max_dispatch_per_poll: int = 20,
    once: bool = False,
    run_agent: bool = False,
    run_deterministic: bool = False,
    sleep_fn: Callable[[float], None] = time.sleep,
    _after_poll: Callable[[int, dict[str, Any]], None] | None = None,
) -> IntentObserverResult:
    """Poll for intents and dispatch bounded edge runs until a stop condition is hit."""

    if poll_interval_seconds < 0:
        raise ValueError("poll_interval_seconds must be >= 0")
    if max_polls is not None and max_polls <= 0:
        raise ValueError("max_polls must be > 0 when provided")
    if idle_polls_before_stop is not None and idle_polls_before_stop <= 0:
        raise ValueError("idle_polls_before_stop must be > 0 when provided")
    if max_dispatch_per_poll <= 0:
        raise ValueError("max_dispatch_per_poll must be > 0")

    polls = 0
    idle_polls = 0
    dispatches: list[dict[str, Any]] = []
    stopped_reason = "completed"

    while True:
        polls += 1
        dispatch_result = gen_dispatch_intents(
            project_root,
            actor=actor,
            max_dispatch=max_dispatch_per_poll,
            run_agent=run_agent,
            run_deterministic=run_deterministic,
        )
        current_dispatches = list(dispatch_result.get("dispatches", []))
        if current_dispatches:
            dispatches.extend(current_dispatches)
            idle_polls = 0
        else:
            idle_polls += 1

        if _after_poll is not None:
            _after_poll(polls, dispatch_result)

        if once:
            stopped_reason = "once"
            break
        if max_polls is not None and polls >= max_polls:
            stopped_reason = "max_polls"
            break
        if idle_polls_before_stop is not None and idle_polls >= idle_polls_before_stop:
            stopped_reason = "idle_threshold"
            break

        sleep_fn(poll_interval_seconds)

    return IntentObserverResult(
        actor=actor,
        polls=polls,
        idle_polls=idle_polls,
        dispatched_count=len(dispatches),
        dispatches=dispatches,
        stopped_reason=stopped_reason,
    )


__all__ = ["IntentObserverResult", "run_intent_observer"]
