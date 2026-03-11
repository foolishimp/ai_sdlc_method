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
    """Request to spawn a child vector \u2014 output of stuck-delta detection."""
    question: str
    parent_feature: str
    triggered_at_edge: str
    vector_type: str = "discovery"  # discovery | spike | poc | hotfix
    context_hints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FoldBackResult:
    """Result of folding a child's results back to parent."""
    parent_id: str
    child_id: str
    payload_path: str
    parent_unblocked: bool
    event_emitted: bool

@dataclass
class InstanceNode:
    """A feature instance positioned on the asset graph topology (derived projection)."""
    feature_id: str
    zoom_level: int
    current_edge: str
    status: str
    delta: int
    parent_id: Optional[str] = None
    converged_edges: List[str] = field(default_factory=list)
    # Hamiltonian H = T + V (ADR-S-020)
    hamiltonian_T: int = 0   # cumulative iteration count (kinetic \u2014 work done)
    hamiltonian_V: int = 0   # current delta >= 0 (potential \u2014 work remaining)

    @property
    def hamiltonian(self) -> int:
        """H = T + V \u2014 total traversal cost at this point in phase space."""
        return self.hamiltonian_T + self.hamiltonian_V

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
class GuardrailResult:
    name: str
    passed: bool
    message: str

@dataclass
class ConstructResult:
    """Result of an artifact construction/modification step."""
    artifact: Optional[str] = None
    reasoning: str = ""
    model: str = "unknown"
    duration_ms: int = 0
    retries: int = 0
    traceability: List[str] = field(default_factory=list)
    source_findings: List[Dict[str, Any]] = field(default_factory=list)
    evaluations: List[FunctorResult] = field(default_factory=list)

@dataclass
class PlanResult:
    """Result of a PLAN functor invocation."""
    units: List[Dict[str, Any]] = field(default_factory=list)
    dep_dag: Dict[str, List[str]] = field(default_factory=dict)
    build_order: List[str] = field(default_factory=list)
    ranked_units: List[str] = field(default_factory=list)
    deferred_units: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""

@dataclass
class WorkOrder:
    """A stable asset produced by the PLAN functor."""
    id: str
    source_asset_id: str
    units: List[Dict[str, Any]]
    dep_dag: Dict[str, List[str]]
    build_order: List[str]
    ranked_units: List[str]
    deferred_units: List[Dict[str, Any]]
    status: str = "pending" # pending, approved, dismissed
    created_at: datetime = field(default_factory=lambda: datetime.now())

@dataclass
class IntentVector:
    """Unified Intent Vector (ADR-S-026)."""
    id: str
    source: str # abiogenesis | gap | parent_vector
    parent_vector_id: Optional[str]
    resolution_level: str # intent | requirements | design | code | deployment | telemetry
    composition_expression: Dict[str, Any] # macro and parameter bindings
    profile: str # full | standard | poc | spike | hotfix | minimal
    vector_type: str # feature | discovery | spike | poc | hotfix
    status: str # pending | iterating | converged | blocked | time_box_expired
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())
    trajectory: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)

@dataclass
class IterationRecord:
    """Record of one iteration \u2014 what happened, what was decided."""
    edge: str
    iteration: int
    report: 'IterationReport'
    event_emitted: bool = True
    construct_result: Optional[ConstructResult] = None
    plan_result: Optional[PlanResult] = None
    # Hamiltonian H = T + V (ADR-S-020)
    hamiltonian_T: int = 0   # cumulative iteration count (kinetic \u2014 work done)
    hamiltonian_V: int = 0   # current delta >= 0 (potential \u2014 work remaining)

    @property
    def converged(self) -> bool:
        return self.report.converged

    @property
    def delta(self) -> int:
        return self.report.delta

    @property
    def guardrail_results(self) -> List[Any]:
        return self.report.guardrail_results

    @property
    def hamiltonian(self) -> int:
        return self.hamiltonian_T + self.hamiltonian_V

@dataclass
class EngineConfig:
    """Configuration for the engine."""
    project_name: str
    workspace_path: Any # Path
    edge_params_dir: Any # Path
    profiles_dir: Any # Path
    constraints: Dict[str, Any]
    graph_topology: Dict[str, Any]
    model: str = "gemini-2.0-flash"
    max_iterations_per_edge: int = 10
    gemini_timeout: int = 300  # v3.0 timeout
    deterministic_only: bool = False
    fd_timeout: int = 120
    stall_timeout: int = 60
    sanitize_env: bool = True
    budget_usd: float = 2.0  # v3.0 budget constraint


@dataclass
class IterationReport:
    asset_path: str
    delta: int
    converged: bool
    functor_results: List[FunctorResult]
    guardrail_results: List[GuardrailResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    spawn: Optional[SpawnRequest] = None
    construct_result: Optional[ConstructResult] = None
    plan_result: Optional[PlanResult] = None

@dataclass
class FeatureTrajectory:
    feature_id: str
    status: str
    trajectory: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class FeatureProposal:
    proposal_id: str
    feature_id: str
    title: str
    description: str
    requirements: List[str]
    intent_id: str
    status: str = "pending" # pending, approved, dismissed

@dataclass
class SpecModification:
    previous_hash: str
    new_hash: str
    delta: str
    trigger_event_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now())
