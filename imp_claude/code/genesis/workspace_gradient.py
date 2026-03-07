# Implements: REQ-LIFE-009 (Spec Review as Gradient Check)
"""Workspace gradient — delta(workspace_state, spec) → work.

Computes the gradient between what the spec asserts and what the workspace
contains. Non-zero delta → potential work (new feature vector, spec update,
orphan cleanup). Zero delta → system at rest.

This is the §7.1 gradient applied at the workspace-spec scale:

    delta(workspace_state, spec_constraints) → classified intents

The computation is:
1. Extract all feature IDs from the specification (FEATURE_VECTORS.md)
2. Extract all feature IDs from the workspace (active + completed)
3. Compute the delta: PENDING (spec → no workspace), ORPHAN (workspace → no spec)
4. Classify each delta item by signal source and severity
5. Generate draft intent_raised proposals for non-zero deltas

Stateless and idempotent: same state + same spec = same intents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml


# ═══════════════════════════════════════════════════════════════════════
# DELTA TYPES
# ═══════════════════════════════════════════════════════════════════════

DELTA_PENDING = "PENDING"  # Spec defines feature, no workspace vector exists
DELTA_ORPHAN = "ORPHAN"  # Workspace vector exists, not in spec
DELTA_STALE = "STALE"  # Workspace vector exists but status is in_progress and very old
DELTA_SPEC_DRIFT = (
    "SPEC_DRIFT"  # Spec file content doesn't match last spec_modified event hash
)
# Implements: REQ-EVOL-NFR-002 (Spec Hash Verification)

# Signal source classification (REQ-LIFE-006)
SIGNAL_GAP = "gap"  # traceability gap
SIGNAL_PROCESS_GAP = "process_gap"  # methodology deficiency
SIGNAL_REFACTORING = "refactoring"  # structural debt

# Severity levels
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"


# ═══════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class DeltaItem:
    """A single non-zero gradient item."""

    delta_type: str  # PENDING | ORPHAN | STALE
    feature_id: str  # REQ key or workspace ID
    signal_source: str  # gap | process_gap | refactoring
    severity: str  # info | warning | critical
    description: str  # human-readable delta description
    recommended_action: str  # what to do about it
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceGradient:
    """Full gradient computation result."""

    spec_count: int
    workspace_count: int
    pending: list[DeltaItem]  # spec → no workspace
    orphans: list[DeltaItem]  # workspace → no spec
    stale: list[DeltaItem]  # workspace → very old in-progress
    total_delta: int  # sum of all non-zero items
    is_at_rest: bool  # total_delta == 0

    def all_items(self) -> list[DeltaItem]:
        return self.pending + self.orphans + self.stale

    def by_severity(self, severity: str) -> list[DeltaItem]:
        return [item for item in self.all_items() if item.severity == severity]

    def summary(self) -> str:
        parts = []
        if self.pending:
            parts.append(f"{len(self.pending)} PENDING")
        if self.orphans:
            parts.append(f"{len(self.orphans)} ORPHAN")
        if self.stale:
            parts.append(f"{len(self.stale)} STALE")
        if not parts:
            return f"delta=0 (workspace at rest — {self.spec_count} spec features, {self.workspace_count} vectors)"
        return (
            f"delta={self.total_delta}: "
            + ", ".join(parts)
            + f" ({self.spec_count} spec, {self.workspace_count} workspace)"
        )


# ═══════════════════════════════════════════════════════════════════════
# SPEC PARSING
# ═══════════════════════════════════════════════════════════════════════

_REQ_KEY_RE = re.compile(r"\bREQ-F-[A-Z]+-\d+\b")


def extract_spec_req_keys(spec_features_path: Path) -> list[str]:
    """Extract all REQ-F-* keys from FEATURE_VECTORS.md."""
    if not spec_features_path.exists():
        return []
    text = spec_features_path.read_text(errors="replace")
    keys = sorted(set(_REQ_KEY_RE.findall(text)))
    return keys


# ═══════════════════════════════════════════════════════════════════════
# WORKSPACE PARSING
# ═══════════════════════════════════════════════════════════════════════


def _load_feature_vector(path: Path) -> Optional[dict[str, Any]]:
    """Load a single feature vector YAML."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return None


def get_workspace_feature_ids(workspace: Path) -> dict[str, dict[str, Any]]:
    """Return {feature_id: vector_data} for all workspace feature vectors.

    Scans both active/ and completed/ directories.
    """
    ws_dir = (
        workspace / ".ai-workspace"
        if (workspace / ".ai-workspace").exists()
        else workspace
    )
    features: dict[str, dict[str, Any]] = {}

    for status_dir in ("active", "completed"):
        fdir = ws_dir / "features" / status_dir
        if not fdir.exists():
            continue
        for fpath in fdir.glob("*.yml"):
            vector = _load_feature_vector(fpath)
            if vector is None:
                continue
            fid = vector.get("id") or vector.get("feature_id") or fpath.stem
            if fid:
                vector["_status_dir"] = status_dir
                vector["_path"] = str(fpath)
                features[fid] = vector

    return features


# ═══════════════════════════════════════════════════════════════════════
# DELTA CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

# Stale threshold: in_progress for more than N days without iteration
_STALE_DAYS_THRESHOLD = 30


def _is_stale(vector: dict[str, Any]) -> bool:
    """Detect if a vector is stuck in in_progress for too long."""
    status = vector.get("status", "")
    if status != "in_progress":
        return False
    # Check last_updated or trajectory timestamps
    last_updated = vector.get("last_updated") or vector.get("updated_at", "")
    if not last_updated:
        return False
    try:
        dt = datetime.fromisoformat(str(last_updated).replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
        return age_days > _STALE_DAYS_THRESHOLD
    except (ValueError, AttributeError):
        return False


def _classify_pending(feature_id: str) -> DeltaItem:
    """Feature defined in spec but no workspace vector → PENDING gap."""
    return DeltaItem(
        delta_type=DELTA_PENDING,
        feature_id=feature_id,
        signal_source=SIGNAL_GAP,
        severity=SEVERITY_WARNING,
        description=f"{feature_id} is defined in the spec but has no workspace vector",
        recommended_action="Run /gen-spawn to create a feature vector, or mark as deferred in the spec",
    )


def _classify_orphan(feature_id: str, vector: dict[str, Any]) -> DeltaItem:
    """Workspace vector exists but feature not in spec → ORPHAN."""
    status_dir = vector.get("_status_dir", "active")
    severity = SEVERITY_INFO if status_dir == "completed" else SEVERITY_WARNING
    return DeltaItem(
        delta_type=DELTA_ORPHAN,
        feature_id=feature_id,
        signal_source=SIGNAL_PROCESS_GAP,
        severity=severity,
        description=f"{feature_id} has a workspace vector ({status_dir}) but is not defined in the spec",
        recommended_action=(
            "Add the feature to specification/features/FEATURE_VECTORS.md, "
            "or archive the workspace vector if the work was abandoned"
        ),
    )


def _classify_stale(feature_id: str, vector: dict[str, Any]) -> DeltaItem:
    """In-progress feature vector with no recent iteration → STALE."""
    return DeltaItem(
        delta_type=DELTA_STALE,
        feature_id=feature_id,
        signal_source=SIGNAL_REFACTORING,
        severity=SEVERITY_WARNING,
        description=f"{feature_id} is in_progress but has not been updated in >{_STALE_DAYS_THRESHOLD} days",
        recommended_action="Resume iteration, mark as blocked, or archive if abandoned",
        extra={"last_updated": vector.get("last_updated", "unknown")},
    )


# ═══════════════════════════════════════════════════════════════════════
# GRADIENT COMPUTATION
# ═══════════════════════════════════════════════════════════════════════


def compute_workspace_gradient(
    workspace: Path,
    spec_features_path: Optional[Path] = None,
) -> WorkspaceGradient:
    """Compute delta(workspace_state, spec) → WorkspaceGradient.

    Stateless and idempotent: same state + same spec = same result.
    """
    # Resolve spec path
    ws_dir = (
        workspace / ".ai-workspace"
        if (workspace / ".ai-workspace").exists()
        else workspace
    )
    if spec_features_path is None:
        project_root = ws_dir.parent if ws_dir.name == ".ai-workspace" else workspace
        spec_features_path = (
            project_root / "specification" / "features" / "FEATURE_VECTORS.md"
        )

    spec_ids = set(extract_spec_req_keys(spec_features_path))
    workspace_vectors = get_workspace_feature_ids(workspace)
    workspace_ids = set(workspace_vectors.keys())

    # PENDING: in spec, not in workspace
    pending_ids = spec_ids - workspace_ids
    pending = [_classify_pending(fid) for fid in sorted(pending_ids)]

    # ORPHAN: in workspace, not in spec
    orphan_ids = workspace_ids - spec_ids
    orphans = [
        _classify_orphan(fid, workspace_vectors[fid]) for fid in sorted(orphan_ids)
    ]

    # STALE: in both, but workspace is stuck
    stale = []
    for fid in sorted(spec_ids & workspace_ids):
        vec = workspace_vectors[fid]
        if _is_stale(vec):
            stale.append(_classify_stale(fid, vec))

    total = len(pending) + len(orphans) + len(stale)
    return WorkspaceGradient(
        spec_count=len(spec_ids),
        workspace_count=len(workspace_ids),
        pending=pending,
        orphans=orphans,
        stale=stale,
        total_delta=total,
        is_at_rest=(total == 0),
    )


# ═══════════════════════════════════════════════════════════════════════
# INTENT PROPOSALS
# ═══════════════════════════════════════════════════════════════════════


def generate_intent_proposals(
    gradient: WorkspaceGradient,
    project: str,
) -> list[dict[str, Any]]:
    """Generate draft intent_raised events for each non-zero delta item.

    These are proposals for human review — not emitted automatically.
    The human decides: create vector, acknowledge, or dismiss.

    Returns list of intent_raised event dicts (not yet written to events.jsonl).
    """
    proposals = []
    now = datetime.now(timezone.utc).isoformat()

    for item in gradient.all_items():
        intent_id = f"INT-GRAD-{item.feature_id}-{item.delta_type}"
        proposals.append(
            {
                "event_type": "intent_raised",
                "timestamp": now,
                "project": project,
                "data": {
                    "intent_id": intent_id,
                    "trigger": f"workspace_gradient_{item.delta_type.lower()}",
                    "delta": item.description,
                    "signal_source": item.signal_source,
                    "vector_type": "feature",
                    "affected_req_keys": [item.feature_id],
                    "severity": item.severity,
                    "recommended_action": item.recommended_action,
                    "draft": True,
                    "causal_chain": {
                        "source": "gen-spec-review",
                        "delta_type": item.delta_type,
                    },
                },
            }
        )

    return proposals
