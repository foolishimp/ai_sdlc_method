
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class Outcome(Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"

@dataclass
class SpawnRequest:
    question: str
    vector_type: str = "discovery"
    context_hints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FunctorResult:
    name: str
    outcome: Outcome
    delta: int
    reasoning: str
    next_candidate: Optional[str] = None
    spawn: Optional[SpawnRequest] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IterationReport:
    asset_path: str
    delta: int
    converged: bool
    functor_results: List[FunctorResult]
    guardrail_results: List[Any] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    spawn: Optional[SpawnRequest] = None

@dataclass
class FeatureTrajectory:
    feature_id: str
    status: str
    trajectory: Dict[str, Dict[str, Any]] = field(default_factory=dict)
