# Implements: REQ-EVAL-001, REQ-ITER-003
"""
AI SDLC Data Models.
Provides strong typing for the Generic SDLC Engine and Functors.
"""

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
    """Signal that a sub-problem requires recursive investigation."""
    question: str
    vector_type: str = "discovery"
    context_hints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FunctorResult:
    """The output of a Generic Predicate (Functor)."""
    name: str
    outcome: Outcome
    delta: int
    reasoning: str
    next_candidate: Optional[str] = None
    spawn: Optional[SpawnRequest] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IterationReport:
    """The consolidated result of one iterate() application."""
    asset_path: str
    delta: int
    converged: bool
    functor_results: List[FunctorResult]
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    spawn: Optional[SpawnRequest] = None

@dataclass
class FeatureTrajectory:
    """Projection of a feature vector's path through the graph."""
    feature_id: str
    status: str
    trajectory: Dict[str, Dict[str, Any]] = field(default_factory=dict)
