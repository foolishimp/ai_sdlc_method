# Implements: REQ-SENSE-001 (Interoceptive Monitoring — INTRO-008 repair affordance)
# Implements: REQ-EVENT-002 (Projection Contract — retroactive convergence evidence)
"""Repair affordance for convergence evidence gaps detected by INTRO-008.

Separation of concerns (ADR-S-037, design v3):
  Detection: workspace_integrity.check_convergence_evidence() / fd_sense.sense_convergence_evidence()
  Repair:    workspace_repair.repair_convergence_evidence()  ← this module

The repair domain is (gap) → event_appended.
The detection domain is (workspace) → list[EvidenceGap].
These are different types. Detection does not imply repair authority.

Repair validity rests on the human's explicit confirmation and provenance record,
not on the existence of a gap plus a boolean.  The repair function constructs the
event; the human attestation is the validity ground.

Invocation surface:
  gen-status --repair   (presents F_H gate, then calls repair_convergence_evidence)
  gen-start Step 10     (detection only — repair is NOT called here)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .workspace_integrity import EvidenceGap


@dataclass
class RepairProvenance:
    """Provenance record for a retroactive repair confirmation.

    The human's explicit attestation is the validity ground — not the gap
    plus a boolean.  The confirmed_by + basis fields record who confirmed
    and on what grounds, making the repair auditable.
    """

    confirmed_by: str          # human ID, session ID, or audit reference
    basis: str                 # why the convergence was valid
    confirmed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    monitor_id: str = "INTRO-008"


@dataclass
class RepairResult:
    """Result of a repair_convergence_evidence() call."""

    repaired: list[str] = field(default_factory=list)    # "feature/edge" strings
    skipped: list[str] = field(default_factory=list)     # gaps not approved
    events_emitted: list[dict] = field(default_factory=list)

    @property
    def repair_count(self) -> int:
        return len(self.repaired)


def repair_convergence_evidence(
    gaps: list[EvidenceGap],
    provenance: RepairProvenance,
    events_path: Path,
    approved: list[str] | None = None,
) -> RepairResult:
    """Emit retroactive edge_converged events for approved evidence gaps.

    Args:
        gaps:        Gaps detected by INTRO-008 (from ConvergenceEvidenceReport.gaps).
        provenance:  Who confirmed the repair and on what grounds.
        events_path: Path to events.jsonl to append events.
        approved:    Optional list of "feature_id/edge" strings to approve.
                     None means all gaps are approved.
                     Empty list means no gaps are approved (dry-run / reject-all).

    Returns:
        RepairResult with per-gap disposition and emitted events.

    Validity contract:
        The emitted edge_converged event is only as truthful as the human's
        attestation.  This function does not re-validate the work — it records
        that the human confirmed the convergence occurred.  The provenance.basis
        field must carry the grounds for that confirmation.
    """
    result = RepairResult()
    now = datetime.now(timezone.utc).isoformat()

    with events_path.open("a", encoding="utf-8") as fh:
        for gap in gaps:
            gap_key = f"{gap.feature_id}/{gap.edge}"

            if approved is not None and gap_key not in approved:
                result.skipped.append(gap_key)
                continue

            event = {
                "event_type": "edge_converged",
                "timestamp": now,
                "project": _read_project_name(events_path),
                "feature": gap.feature_id,
                "edge": gap.edge,
                "executor": "human",
                "emission": "retroactive",
                "data": {
                    "convergence_type": "retroactive_repair",
                    "confirmed_by": provenance.confirmed_by,
                    "confirmed_at": provenance.confirmed_at,
                    "basis": provenance.basis,
                    "monitor_id": provenance.monitor_id,
                    "repaired_at": now,
                },
            }
            fh.write(json.dumps(event) + "\n")
            result.repaired.append(gap_key)
            result.events_emitted.append(event)

    return result


def format_repair_prompt(gaps: list[EvidenceGap]) -> str:
    """Format the F_H gate prompt for human confirmation.

    Returns a string suitable for display to the human before calling
    repair_convergence_evidence().  Does not emit events or mutate state.
    """
    lines = [
        f"PROJECTION AUTHORITY REPAIR — {len(gaps)} gap(s) detected by INTRO-008",
        "",
    ]
    for i, gap in enumerate(gaps, 1):
        lines += [
            f"  Gap {i}: {gap.feature_id} / {gap.edge}",
            f"    Claim:  workspace YAML status=converged",
            f"    Evidence: no edge_converged terminal event in stream",
            f"    Action if approved: append edge_converged{{emission: retroactive, executor: human}}",
            "",
        ]
    lines += [
        "  These gaps predate the INTRO-008 enforcement check.",
        "  Retroactive closure records that convergence occurred; it does not re-validate the work.",
        "  The validity of each repair rests on the accuracy of your confirmation.",
        "",
        "  Confirm repairs? [y/n/selective]",
        "  (y = approve all, n = reject all, selective = approve per gap)",
    ]
    return "\n".join(lines)


def _read_project_name(events_path: Path) -> str:
    """Extract project name from the first event in the log."""
    try:
        with events_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    event = json.loads(line)
                    return event.get("project", "")
    except (OSError, json.JSONDecodeError):
        pass
    return ""
