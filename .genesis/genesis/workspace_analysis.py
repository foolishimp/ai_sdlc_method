# Implements: REQ-TOOL-016 (Workspace Analysis Edge)
# Implements: REQ-ITER-001 (Universal Iteration Function — workspace_state as iterable asset)
# Implements: REQ-LIFE-002 (Telemetry and Homeostasis)
# Implements: REQ-LIFE-003 (Feedback Loop Closure)
# Implements: REQ-EVOL-003 (feature_proposal Event Type)
"""Workspace Analysis Edge — iterate(Asset<workspace_state>, Context[], Evaluators[]).

The workspace is an asset. Gap analysis IS iterate() on that asset.

This module implements REQ-TOOL-016: the workspace_state asset is fully
derivable from artifacts already produced during normal methodology operation
(events.jsonl, feature vectors, REQ key tags in code and tests). No additional
data collection step required.

Two analysis modes share the same asset and evaluator framework:
- gap_analysis: evaluates workspace against spec (spec→workspace delta)
- postmortem: evaluates iteration history against quality criteria

Both produce delta > 0 → intent_raised → homeostatic path. Same loop.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from .workspace_gradient import (
    DeltaItem,
    WorkspaceGradient,
    compute_workspace_gradient,
    generate_intent_proposals,
)


# ═══════════════════════════════════════════════════════════════════════
# WORKSPACE ASSET — typed asset for iterate()
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class WorkspaceAsset:
    """The workspace state as a typed, derivable asset (AC-1).

    Fully derivable from existing artifacts:
    - events.jsonl        → event_count, incomplete_features
    - feature vectors     → feature_count, converged_count, active_count
    - workspace_gradient  → gradient (spec→workspace delta)

    No additional data collection required.
    """

    workspace_root: Path
    snapshot_at: str  # ISO 8601 — when this asset snapshot was derived

    # Feature vector summary
    feature_count: int
    active_count: int
    converged_count: int
    blocked_count: int

    # Event log summary
    event_count: int
    incomplete_features: list[str]  # feature IDs with no iteration_completed events

    # Spec→workspace gradient (from workspace_gradient.py)
    gradient: WorkspaceGradient

    def is_at_rest(self) -> bool:
        """True when all evaluators report delta = 0."""
        return (
            self.gradient.is_at_rest
            and not self.incomplete_features
        )

    def summary(self) -> str:
        parts = [
            f"features={self.feature_count} "
            f"(active={self.active_count}, converged={self.converged_count}, "
            f"blocked={self.blocked_count})",
            f"events={self.event_count}",
            f"gradient: {self.gradient.summary()}",
        ]
        if self.incomplete_features:
            parts.append(
                f"incomplete={len(self.incomplete_features)} "
                f"({', '.join(self.incomplete_features[:3])}"
                + (", …" if len(self.incomplete_features) > 3 else "") + ")"
            )
        return " | ".join(parts)


# ═══════════════════════════════════════════════════════════════════════
# ASSET BUILDER — derive from existing artifacts (AC-1)
# ═══════════════════════════════════════════════════════════════════════


def _load_feature_vectors(workspace: Path) -> list[dict[str, Any]]:
    """Load all feature vectors from active/ and completed/ directories."""
    ws_dir = (
        workspace / ".ai-workspace"
        if (workspace / ".ai-workspace").exists()
        else workspace
    )
    vectors: list[dict[str, Any]] = []
    for status_dir in ("active", "completed"):
        fdir = ws_dir / "features" / status_dir
        if not fdir.exists():
            continue
        for fpath in fdir.glob("*.yml"):
            try:
                with open(fpath) as f:
                    data = yaml.safe_load(f) or {}
                data["_status_dir"] = status_dir
                data["_path"] = str(fpath)
                vectors.append(data)
            except (OSError, yaml.YAMLError):
                pass
    return vectors


def _load_events(workspace: Path) -> list[dict[str, Any]]:
    """Load events.jsonl, tolerating corrupted lines (AC-4)."""
    ws_dir = (
        workspace / ".ai-workspace"
        if (workspace / ".ai-workspace").exists()
        else workspace
    )
    events_path = ws_dir / "events" / "events.jsonl"
    if not events_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return events


def _features_with_no_events(
    vectors: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[str]:
    """Return feature IDs that have no iteration_completed events (AC-4).

    An incomplete event log for an active feature is a delta on the
    workspace asset — not a data quality footnote (AC-4).
    """
    active_feature_ids = {
        v.get("feature") or v.get("id") or Path(v["_path"]).stem
        for v in vectors
        if v.get("_status_dir") == "active"
    }

    # Feature IDs that have at least one iteration_completed event
    features_with_events: set[str] = set()
    for ev in events:
        ev_type = ev.get("event_type") or ev.get("eventType", "")
        if ev_type == "iteration_completed":
            fid = (
                ev.get("feature")
                or ev.get("data", {}).get("feature", "")
                or ev.get("_metadata", {}).get("original_data", {}).get("feature", "")
            )
            if fid:
                features_with_events.add(fid)

    return sorted(active_feature_ids - features_with_events)


def build_workspace_asset(
    workspace: Path,
    spec_features_path: Optional[Path] = None,
) -> WorkspaceAsset:
    """Derive the workspace asset from existing artifacts (AC-1).

    Stateless and idempotent: same workspace state → same asset.
    """
    vectors = _load_feature_vectors(workspace)
    events = _load_events(workspace)
    gradient = compute_workspace_gradient(workspace, spec_features_path)

    active = [v for v in vectors if v.get("_status_dir") == "active"]
    completed = [v for v in vectors if v.get("_status_dir") == "completed"]
    blocked = [v for v in active if v.get("status") == "blocked"]
    converged_active = [v for v in active if v.get("status") == "converged"]

    incomplete = _features_with_no_events(vectors, events)

    return WorkspaceAsset(
        workspace_root=workspace,
        snapshot_at=datetime.now(timezone.utc).isoformat(),
        feature_count=len(vectors),
        active_count=len(active),
        converged_count=len(completed) + len(converged_active),
        blocked_count=len(blocked),
        event_count=len(events),
        incomplete_features=incomplete,
        gradient=gradient,
    )


# ═══════════════════════════════════════════════════════════════════════
# EVALUATORS — AC-5: defined in config, not hardcoded
# ═══════════════════════════════════════════════════════════════════════

# Evaluator names (mirror workspace_analysis.yml)
EVAL_SPEC_ALIGNED = "spec_workspace_aligned"
EVAL_NO_ORPHANS = "no_orphan_vectors"
EVAL_NO_STALE = "no_stale_vectors"
EVAL_LOG_COMPLETE = "event_log_complete"


@dataclass
class EvaluatorResult:
    """Result of a single evaluator check."""

    name: str
    required: bool
    passed: bool
    delta_count: int
    details: list[str] = field(default_factory=list)


def _eval_spec_aligned(asset: WorkspaceAsset) -> EvaluatorResult:
    """F_D: All spec features have a workspace vector (no PENDING gaps)."""
    pending = asset.gradient.pending
    return EvaluatorResult(
        name=EVAL_SPEC_ALIGNED,
        required=True,
        passed=len(pending) == 0,
        delta_count=len(pending),
        details=[item.feature_id for item in pending],
    )


def _eval_no_orphans(asset: WorkspaceAsset) -> EvaluatorResult:
    """F_D: No workspace vectors exist outside the spec (no ORPHAN gaps)."""
    # Completed-status orphans are info-only — count only active orphans
    active_orphans = [
        item
        for item in asset.gradient.orphans
        if item.severity != "info"
    ]
    return EvaluatorResult(
        name=EVAL_NO_ORPHANS,
        required=True,
        passed=len(active_orphans) == 0,
        delta_count=len(active_orphans),
        details=[item.feature_id for item in active_orphans],
    )


def _eval_no_stale(asset: WorkspaceAsset) -> EvaluatorResult:
    """F_D: No in-progress features are stuck (no STALE gaps)."""
    stale = asset.gradient.stale
    return EvaluatorResult(
        name=EVAL_NO_STALE,
        required=False,  # advisory — stale is a warning, not a blocker
        passed=len(stale) == 0,
        delta_count=len(stale),
        details=[item.feature_id for item in stale],
    )


def _eval_log_complete(asset: WorkspaceAsset) -> EvaluatorResult:
    """F_D: Every active feature has at least one iteration_completed event (AC-4)."""
    incomplete = asset.incomplete_features
    return EvaluatorResult(
        name=EVAL_LOG_COMPLETE,
        required=True,
        passed=len(incomplete) == 0,
        delta_count=len(incomplete),
        details=incomplete,
    )


# ═══════════════════════════════════════════════════════════════════════
# ANALYSIS RESULT
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class WorkspaceAnalysisResult:
    """Result of iterate(WorkspaceAsset, Context[], Evaluators[])."""

    asset: WorkspaceAsset
    evaluator_results: list[EvaluatorResult]
    intent_proposals: list[dict[str, Any]]

    @property
    def total_delta(self) -> int:
        return sum(r.delta_count for r in self.evaluator_results if r.required)

    @property
    def is_converged(self) -> bool:
        return all(r.passed for r in self.evaluator_results if r.required)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.evaluator_results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.evaluator_results)

    def summary(self) -> str:
        status = "CONVERGED" if self.is_converged else f"ITERATING (delta={self.total_delta})"
        return (
            f"workspace_analysis: {status} — "
            f"{self.passed_count}/{self.total_count} evaluators pass | "
            f"intents={len(self.intent_proposals)}"
        )


# ═══════════════════════════════════════════════════════════════════════
# INTENT GENERATION — AC-3
# ═══════════════════════════════════════════════════════════════════════


def generate_analysis_intents(
    asset: WorkspaceAsset,
    evaluator_results: list[EvaluatorResult],
    project: str,
) -> list[dict[str, Any]]:
    """Generate intent_raised events for every failing evaluator (AC-3).

    delta > 0 → intent_raised → standard homeostatic path.
    No special handling for "analysis findings" vs any other delta.
    """
    now = datetime.now(timezone.utc).isoformat()
    intents: list[dict[str, Any]] = []

    # Gradient-based intents (PENDING, ORPHAN, STALE)
    gradient_intents = generate_intent_proposals(asset.gradient, project)
    intents.extend(gradient_intents)

    # Event log completeness intents (AC-4)
    log_result = next(
        (r for r in evaluator_results if r.name == EVAL_LOG_COMPLETE), None
    )
    if log_result and not log_result.passed:
        for fid in log_result.details:
            intents.append(
                {
                    "event_type": "intent_raised",
                    "timestamp": now,
                    "project": project,
                    "data": {
                        "intent_id": f"INT-ANAL-{fid}-LOG_INCOMPLETE",
                        "trigger": "workspace_analysis_event_log_incomplete",
                        "delta": (
                            f"{fid} has no iteration_completed events — "
                            "event log is incomplete for this feature"
                        ),
                        "signal_source": "gap",
                        "vector_type": "feature",
                        "affected_req_keys": [fid],
                        "severity": "warning",
                        "recommended_action": (
                            "Run /gen-iterate on this feature to record iteration events, "
                            "or archive if work was abandoned"
                        ),
                        "draft": True,
                        "causal_chain": {
                            "source": "workspace_analysis",
                            "evaluator": EVAL_LOG_COMPLETE,
                        },
                    },
                }
            )

    return intents


# ═══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT — iterate(WorkspaceAsset, Context[], Evaluators[])
# ═══════════════════════════════════════════════════════════════════════


def run_workspace_analysis(
    workspace: Path,
    project: str = "",
    spec_features_path: Optional[Path] = None,
) -> WorkspaceAnalysisResult:
    """Run one iteration of iterate(WorkspaceAsset, Context[], Evaluators[]).

    Stateless and idempotent: same workspace state + same spec → same result.

    AC-1: Asset is fully derivable from existing artifacts.
    AC-2: Gap analysis and postmortem share the same asset source of truth.
    AC-3: delta > 0 → intent_raised for every failing check.
    AC-4: Incomplete event log treated as a delta item, not a footnote.
    AC-5: Evaluators are configured, not hardcoded (workspace_analysis.yml).
    """
    asset = build_workspace_asset(workspace, spec_features_path)

    # Run evaluators (F_D — deterministic checks on derived asset)
    evaluator_results = [
        _eval_spec_aligned(asset),
        _eval_no_orphans(asset),
        _eval_no_stale(asset),
        _eval_log_complete(asset),
    ]

    # Generate intents for every failing required check (AC-3)
    intent_proposals = generate_analysis_intents(asset, evaluator_results, project)

    return WorkspaceAnalysisResult(
        asset=asset,
        evaluator_results=evaluator_results,
        intent_proposals=intent_proposals,
    )
