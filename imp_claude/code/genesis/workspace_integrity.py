# Implements: REQ-SENSE-001 (Interoceptive Monitoring — INTRO-008 convergence_evidence_present)
# Implements: REQ-EVENT-002 (Projection Contract — Projection Authority enforcement)
# Implements: REQ-LIFE-006 (Signal Source Classification — convergence_without_evidence)
"""INTRO-008: convergence_evidence_present F_D check.

Implements ADR-S-037 §2: for each feature vector with a converged edge, verify
the event stream contains a terminal convergence event (edge_converged /
ConvergenceAchieved) for that feature+edge.

Output contract (Option A — triage-mediated):
    check() → list[EvidenceGap]

The caller (sensory service) emits interoceptive_signal per gap; affect triage
routes to intent_raised{signal_source: convergence_without_evidence}.
The check itself never emits intent_raised directly.

Terminal convergence events (per REQ-EVENT-003 taxonomy):
    Canonical:            ConvergenceAchieved
    imp_claude binding:   edge_converged

NOT terminal (lifecycle events — do not satisfy the check):
    IterationCompleted / iteration_completed
    IterationStarted  / edge_started
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml


# ── Event types that constitute terminal convergence evidence ─────────────────
TERMINAL_CONVERGENCE_EVENTS: frozenset[str] = frozenset(
    {
        "edge_converged",        # imp_claude binding
        "ConvergenceAchieved",   # REQ-EVENT-003 canonical
    }
)

# ── Event types that are lifecycle events, NOT terminal convergence ───────────
LIFECYCLE_ONLY_EVENTS: frozenset[str] = frozenset(
    {
        "iteration_completed",
        "IterationCompleted",
        "edge_started",
        "EdgeStarted",
        "iteration_started",
        "IterationStarted",
    }
)


@dataclass(frozen=True)
class EvidenceGap:
    """A converged edge with no terminal convergence event in the stream."""

    feature_id: str
    edge: str
    vector_path: Path
    claimed_status: str = "converged"

    def as_interoceptive_signal(self) -> dict:
        """Format for interoceptive_signal event emission (sensory service responsibility)."""
        return {
            "monitor_id": "INTRO-008",
            "severity": "critical",
            "observation": "convergence_without_evidence",
            "affected_features": [self.feature_id],
            "edge": self.edge,
            "detail": (
                f"{self.feature_id}/{self.edge} claims converged "
                "but no terminal convergence event found in stream"
            ),
        }


@dataclass
class ConvergenceEvidenceReport:
    """Result of running convergence_evidence_present across a workspace."""

    gaps: list[EvidenceGap] = field(default_factory=list)
    checked_edges: int = 0
    checked_features: int = 0

    @property
    def passed(self) -> bool:
        return len(self.gaps) == 0

    @property
    def delta(self) -> int:
        return len(self.gaps)


def _iter_feature_vectors(workspace_root: Path) -> Iterator[tuple[Path, dict]]:
    """Yield (path, parsed_yaml) for all feature vectors in active/ and completed/."""
    features_root = workspace_root / ".ai-workspace" / "features"
    for subdir in ("active", "completed"):
        folder = features_root / subdir
        if not folder.exists():
            continue
        for yml_path in sorted(folder.glob("*.yml")):
            try:
                data = yaml.safe_load(yml_path.read_text()) or {}
            except Exception:
                continue
            yield yml_path, data


def _extract_feature_id(data: dict, path: Path) -> str | None:
    """Extract canonical feature ID from a vector YAML."""
    # Flat format: feature: REQ-F-...
    fid = data.get("feature") or data.get("id")
    if isinstance(fid, str) and fid.strip():
        return fid.strip()
    # Nested format: feature: {id: ...}
    if isinstance(fid, dict):
        return fid.get("id", "").strip() or None
    # Fall back to filename stem
    return path.stem


def _converged_edges(data: dict) -> list[str]:
    """Return edge names where trajectory status is 'converged'."""
    trajectory = data.get("trajectory", {})
    if not isinstance(trajectory, dict):
        return []
    return [
        edge
        for edge, info in trajectory.items()
        if isinstance(info, dict) and info.get("status") == "converged"
    ]


def _load_events(events_path: Path) -> list[dict]:
    """Load events.jsonl — returns empty list on missing or corrupt file."""
    if not events_path.exists():
        return []
    events = []
    for line in events_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _has_terminal_convergence_event(
    events: list[dict],
    feature_id: str,
    edge: str,
) -> bool:
    """Return True if events contains a terminal convergence event for feature_id+edge.

    Matching rules (OR logic — any of these is sufficient):
      event_type in TERMINAL_CONVERGENCE_EVENTS
      AND (feature == feature_id OR instance_id == feature_id)
      AND edge == edge_name

    The feature ID is matched against both the top-level 'feature' field and
    the 'instance_id' field (for OL-format events where instance_id carries the
    feature context).
    """
    for event in events:
        et = event.get("event_type") or event.get("eventType", "")
        if et not in TERMINAL_CONVERGENCE_EVENTS:
            continue

        # Feature matching: top-level 'feature' field or OL 'instance_id'
        ev_feature = event.get("feature") or event.get("instance_id", "")
        # Also check inside 'data' payload for either field
        data = event.get("data", {}) or {}
        ev_feature_data = data.get("feature") or data.get("instance_id", "")
        matched_feature = ev_feature == feature_id or ev_feature_data == feature_id

        if not matched_feature:
            continue

        # Edge matching: top-level 'edge' field or inside 'data'
        ev_edge = event.get("edge") or data.get("edge", "")
        if ev_edge == edge:
            return True

    return False


def check_convergence_evidence(
    workspace_root: Path,
    events_path: Path | None = None,
) -> ConvergenceEvidenceReport:
    """INTRO-008: convergence_evidence_present F_D check.

    Scans all feature vectors (active + completed) for edges claiming
    status: converged with no terminal convergence event in the stream.

    Args:
        workspace_root: Project root (parent of .ai-workspace/).
        events_path: Path to events.jsonl. Defaults to
                     workspace_root/.ai-workspace/events/events.jsonl.

    Returns:
        ConvergenceEvidenceReport with gaps list and summary counts.
        report.passed == True means all converged edges have stream evidence.
    """
    if events_path is None:
        events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"

    events = _load_events(events_path)
    report = ConvergenceEvidenceReport()

    for vector_path, vector_data in _iter_feature_vectors(workspace_root):
        feature_id = _extract_feature_id(vector_data, vector_path)
        if not feature_id:
            continue

        report.checked_features += 1
        converged = _converged_edges(vector_data)

        for edge in converged:
            report.checked_edges += 1
            if not _has_terminal_convergence_event(events, feature_id, edge):
                report.gaps.append(
                    EvidenceGap(
                        feature_id=feature_id,
                        edge=edge,
                        vector_path=vector_path,
                    )
                )

    return report
