# Implements: GENESIS_ENGINE_SPEC §1 (Data Model)
"""Data models for the Genesis Engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Category(Enum):
    """Functor category — how a functional unit is rendered."""

    F_D = "F_D"  # deterministic
    F_P = "F_P"  # probabilistic (agent/LLM)
    F_H = "F_H"  # human


class FunctionalUnit(Enum):
    """The 8 functional units of the methodology."""

    EVALUATE = "evaluate"
    CONSTRUCT = "construct"
    CLASSIFY = "classify"
    ROUTE = "route"
    PROPOSE = "propose"
    SENSE = "sense"
    EMIT = "emit"
    DECIDE = "decide"


# Category-fixed units (spec §2.9)
CATEGORY_FIXED = {
    FunctionalUnit.EMIT: Category.F_D,
    FunctionalUnit.DECIDE: Category.F_H,
}


class CheckOutcome(Enum):
    """Result of evaluating a single check."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class ResolvedCheck:
    """A checklist entry with all $variables resolved."""

    name: str
    check_type: str  # "deterministic" | "agent" | "human"
    functional_unit: str
    criterion: str
    source: str
    required: bool
    command: Optional[str] = None
    pass_criterion: Optional[str] = None
    unresolved: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Outcome of running one check."""

    name: str
    outcome: CheckOutcome
    required: bool
    check_type: str
    functional_unit: str
    message: str = ""
    command: str = ""
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""


@dataclass
class EvaluationResult:
    """Aggregate result of evaluating all checks on one edge."""

    edge: str
    checks: list[CheckResult] = field(default_factory=list)
    delta: int = 0
    converged: bool = False
    escalations: list[str] = field(default_factory=list)
    spawn_requested: str = ""


@dataclass
class RouteResult:
    """Output of F_D route."""

    selected_edge: str
    reason: str
    profile: str
    candidates: list[str] = field(default_factory=list)


@dataclass
class SpawnRequest:
    """Request to spawn a child vector."""

    question: str
    vector_type: str
    parent_feature: str
    triggered_at_edge: str
    context_hints: dict = field(default_factory=dict)


@dataclass
class SpawnResult:
    """Result of creating a child vector."""

    child_id: str
    child_path: str
    parent_updated: bool
    event_emitted: bool
    profile: str


@dataclass
class FoldBackResult:
    """Result of folding a child's results back to parent."""

    parent_id: str
    child_id: str
    payload_path: str
    parent_unblocked: bool
    event_emitted: bool


@dataclass
class Event:
    """Structured event for events.jsonl."""

    event_type: str
    timestamp: str
    project: str
    data: dict = field(default_factory=dict)
