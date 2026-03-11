"""Pydantic models defining the OpenAPI response schema for Genesis Navigator.

All models are read-only projections of workspace state.
"""

# Implements: REQ-F-API-001
# Implements: REQ-F-API-002
# Implements: REQ-F-STAT-001
# Implements: REQ-F-STAT-002
# Implements: REQ-F-STAT-003
# Implements: REQ-F-STAT-004
# Implements: REQ-F-FEATDETAIL-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProjectState(str, Enum):
    """Lifecycle state of a Genesis project workspace."""

    ITERATING = "ITERATING"
    QUIESCENT = "QUIESCENT"
    CONVERGED = "CONVERGED"
    BOUNDED = "BOUNDED"
    UNINITIALIZED = "uninitialized"


class ProjectSummary(BaseModel):
    """Summary of a single Genesis project returned by GET /api/projects."""

    project_id: str = Field(
        ..., description="Unique project identifier derived from directory name."
    )
    name: str = Field(..., description="Human-readable project name (directory name).")
    path: str = Field(..., description="Absolute filesystem path to the project root.")
    state: ProjectState = Field(..., description="Computed lifecycle state.")
    active_feature_count: int = Field(
        ..., description="Number of YAML files in .ai-workspace/features/active/."
    )
    converged_feature_count: int = Field(
        ..., description="Number of YAML files in .ai-workspace/features/completed/."
    )
    last_event_at: Optional[str] = Field(
        None, description="ISO 8601 timestamp of the most recent event in events.jsonl."
    )
    scan_duration_ms: float = Field(
        ..., description="Time taken to scan and compute this project entry, in milliseconds."
    )


class EdgeTrajectory(BaseModel):
    """Convergence trajectory for a single graph edge within a feature."""

    edge: str = Field(..., description="Edge identifier (e.g. 'design→code').")
    status: str = Field(..., description="'converged' or 'in_progress'.")
    iteration: int = Field(..., description="Number of iterate() calls on this edge.")
    delta: int = Field(..., description="Last observed delta value (0 when converged).")
    started_at: Optional[str] = Field(None, description="ISO 8601 timestamp of edge_started.")
    converged_at: Optional[str] = Field(None, description="ISO 8601 timestamp of edge_converged.")


class FeatureDetail(BaseModel):
    """Full detail for a single feature vector including Hamiltonian metrics."""

    feature_id: str = Field(..., description="Feature identifier (REQ key or directory stem).")
    title: str = Field(..., description="Human-readable feature title.")
    status: str = Field(..., description="Feature lifecycle status from YAML.")
    current_edge: Optional[str] = Field(
        None, description="The edge currently being iterated, if any."
    )
    delta: int = Field(..., description="Current delta (V component of Hamiltonian).")
    hamiltonian: dict[str, Any] = Field(
        ..., description="Hamiltonian dict with keys H, T, V, flat."
    )
    trajectory: list[EdgeTrajectory] = Field(
        default_factory=list, description="Ordered list of edge trajectories."
    )
    error: Optional[str] = Field(
        None, description="Parse error message if feature YAML was malformed."
    )
    satisfies: list[str] = Field(
        default_factory=list, description="REQ keys this feature satisfies."
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Acceptance criteria from feature vector constraints."
    )


class ProjectDetail(BaseModel):
    """Full detail for a single Genesis project, including all feature vectors."""

    project_id: str = Field(..., description="Unique project identifier.")
    name: str = Field(..., description="Human-readable project name (directory name).")
    state: str = Field(..., description="Computed lifecycle state string.")
    features: list[FeatureDetail] = Field(
        default_factory=list, description="All feature vectors with detail."
    )
    total_edges: int = Field(..., description="Sum of all edge trajectory entries.")
    converged_edges: int = Field(
        ..., description="Number of edge trajectories with status 'converged'."
    )


# ---------------------------------------------------------------------------
# Gap Analysis models (REQ-F-GAPENGINE-001)
# ---------------------------------------------------------------------------


class GapItem(BaseModel):
    """A single traceability gap — one uncovered REQ key."""

    req_key: str = Field(..., description="The REQ-* key that is not covered.")
    gap_type: str = Field(
        ..., description="Gap type: CODE_GAP, TEST_GAP, TELEMETRY_GAP, or ORPHAN."
    )
    files: list[str] = Field(
        default_factory=list, description="Files where the key appears (if any)."
    )
    suggested_command: Optional[str] = Field(
        None, description="Suggested genesis command to close this gap."
    )


class GapLayer(BaseModel):
    """Aggregated gap data for one traceability layer."""

    gap_count: int = Field(..., description="Number of uncovered REQ keys.")
    coverage_pct: float = Field(..., description="Percentage of spec keys covered (0.0–100.0).")
    gaps: list[GapItem] = Field(default_factory=list, description="Individual gap items.")


class GapReport(BaseModel):
    """Full gap analysis report for one project."""

    project_id: str = Field(..., description="Project identifier.")
    computed_at: str = Field(..., description="ISO 8601 UTC timestamp of computation.")
    health_signal: str = Field(..., description="GREEN / AMBER / RED based on combined gap count.")
    layer_1: GapLayer = Field(..., description="Layer 1: code tag coverage (# Implements: REQ-*).")
    layer_2: GapLayer = Field(..., description="Layer 2: test tag coverage (# Validates: REQ-*).")
    layer_3: GapLayer = Field(..., description="Layer 3: telemetry tag coverage (req='REQ-*').")


# ---------------------------------------------------------------------------
# Decision Queue models (REQ-F-QUEUEENGINE-001)
# ---------------------------------------------------------------------------


class QueueItemDetail(BaseModel):
    """Detailed context for a single decision queue item."""

    reason: str = Field(..., description="Human-readable explanation of why this item is queued.")
    delta: Optional[int] = Field(
        None, description="Current delta (V component) for iterating features."
    )
    failing_checks: list[str] = Field(
        default_factory=list, description="List of failing evaluator checks."
    )
    expected_outcome: str = Field(
        ..., description="What the suggested command is expected to produce."
    )
    gap_keys: list[str] = Field(
        default_factory=list, description="REQ keys in this gap cluster (GAP_CLUSTER items)."
    )
    iteration_history: list[int] = Field(
        default_factory=list, description="Last 3 delta values for stuck features."
    )


class QueueItem(BaseModel):
    """A single item in the project decision queue."""

    type: str = Field(
        ..., description="Item type: STUCK, BLOCKED, GAP_CLUSTER, IN_PROGRESS, or healthy."
    )
    severity: str = Field(..., description="Severity: critical, high, medium, low, or info.")
    feature_id: Optional[str] = Field(
        None, description="Associated feature identifier (if applicable)."
    )
    description: str = Field(..., description="One-line human-readable description.")
    command: str = Field(..., description="Suggested genesis command to act on this item.")
    detail: QueueItemDetail = Field(..., description="Expanded detail for the item.")
