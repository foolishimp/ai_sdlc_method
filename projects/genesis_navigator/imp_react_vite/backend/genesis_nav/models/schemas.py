"""Pydantic models defining the OpenAPI response schema for Genesis Navigator.

All models are read-only projections of workspace state.
"""

# Implements: REQ-F-API-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from enum import Enum
from typing import Optional

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
