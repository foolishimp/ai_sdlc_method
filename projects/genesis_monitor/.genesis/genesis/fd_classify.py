# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-COORD-002 (Feature Assignment via Events)
# Implements: REQ-EDGE-004 (Code Tagging), REQ-LIFE-006 (Signal Source Classification)
"""F_D classify — deterministic classification of REQ tags, source findings, signals."""

import re

from .models import ClassificationResult

_REQ_TAG_PATTERN = re.compile(r"(Implements|Validates):\s*REQ-[A-Z]+(?:-[A-Z]+)*-\d+")

_REQ_KEY_PATTERN = re.compile(r"REQ-[A-Z]+(?:-[A-Z]+)*-\d+")

# Keyword sets for source finding classification
_AMBIGUITY_KEYWORDS = {
    "unclear",
    "ambiguous",
    "vague",
    "undefined",
    "unspecified",
    "unknown",
    "uncertain",
    "implicit",
    "assumed",
    "tbd",
}
_GAP_KEYWORDS = {
    "missing",
    "absent",
    "gap",
    "omitted",
    "incomplete",
    "no mention",
    "not defined",
    "not specified",
    "lacks",
}
_UNDERSPEC_KEYWORDS = {
    "underspecified",
    "under-specified",
    "insufficient detail",
    "needs clarification",
    "needs refinement",
    "placeholder",
}


def classify_req_tag(text: str) -> ClassificationResult:
    """Validate a REQ tag string against the expected format.

    Returns classification: VALID, INVALID_FORMAT, or MISSING.
    """
    text = text.strip()
    if not text:
        return ClassificationResult(
            input_text=text,
            classification="MISSING",
            evidence="Empty input",
        )

    if _REQ_TAG_PATTERN.search(text):
        return ClassificationResult(
            input_text=text,
            classification="VALID",
            evidence=f"Matches pattern: {_REQ_TAG_PATTERN.pattern}",
        )

    # Check if there's a REQ key but wrong format
    if _REQ_KEY_PATTERN.search(text):
        return ClassificationResult(
            input_text=text,
            classification="INVALID_FORMAT",
            evidence="REQ key found but missing 'Implements:' or 'Validates:' prefix",
        )

    return ClassificationResult(
        input_text=text,
        classification="MISSING",
        evidence="No REQ tag found",
    )


def classify_source_finding(description: str) -> ClassificationResult:
    """Classify a source analysis finding by keyword matching.

    Returns: SOURCE_AMBIGUITY, SOURCE_GAP, SOURCE_UNDERSPEC, or UNCLASSIFIED.
    """
    lower = description.lower()

    for kw in _UNDERSPEC_KEYWORDS:
        if kw in lower:
            return ClassificationResult(
                input_text=description,
                classification="SOURCE_UNDERSPEC",
                evidence=f"Matched keyword: '{kw}'",
            )

    for kw in _AMBIGUITY_KEYWORDS:
        if kw in lower:
            return ClassificationResult(
                input_text=description,
                classification="SOURCE_AMBIGUITY",
                evidence=f"Matched keyword: '{kw}'",
            )

    for kw in _GAP_KEYWORDS:
        if kw in lower:
            return ClassificationResult(
                input_text=description,
                classification="SOURCE_GAP",
                evidence=f"Matched keyword: '{kw}'",
            )

    return ClassificationResult(
        input_text=description,
        classification="UNCLASSIFIED",
        evidence="No classification keywords matched",
    )


def classify_signal_source(event: dict) -> str:
    """Deterministic signal source classification from event fields.

    Maps event_type to signal source category. Falls back to OL eventType
    for raw OL events that normalize_event could not convert (no sdlc:event_type facet).
    """
    event_type = event.get("event_type", "")

    signal_map = {
        # Core iteration lifecycle
        "iteration_started": "iteration",
        "iteration_completed": "iteration",
        "iteration_failed": "failure",
        "iteration_abandoned": "iteration",
        # Edge lifecycle
        "edge_started": "edge_transition",
        "edge_converged": "convergence",
        # Spawn lifecycle
        "spawn_created": "spawn",
        "spawn_folded_back": "spawn",
        "feature_spawned": "spawn",
        # Convergence / evaluation
        "evaluator_voted": "evaluation",
        "evaluator_ran": "evaluation",
        "evaluator_detail": "evaluation",
        "consensus_reached": "convergence",
        "convergence_achieved": "convergence",
        # Coordination (ADR-013)
        "edge_claim": "coordination",
        "edge_claimed": "coordination",
        "claim_rejected": "coordination",
        "claim_expired": "coordination",
        "edge_released": "coordination",
        "convergence_escalated": "escalation",
        # Escalation / encoding
        "encoding_escalated": "escalation",
        "transition_authorized": "convergence",
        "transition_denied": "failure",
        # Consciousness loop / proposals (ADR-011)
        "feature_proposal": "proposal",
        "feature_proposed": "proposal",
        "feature_approved": "proposal",
        "feature_dismissed": "proposal",
        "feature_proposal_dismissed": "proposal",
        # Spec evolution (REQ-EVOL-004)
        "spec_modified": "spec_evolution",
        # Sensory systems (REQ-SENSE-*)
        "telemetry_signal_emitted": "telemetry",
        "exteroceptive_signal": "sensory",
        "observer_signal": "sensory",
        # Intent / homeostasis
        "intent_raised": event.get("data", {}).get("signal_source", "homeostasis"),
        "finding_raised": "health",
        # Lifecycle
        "project_initialized": "lifecycle",
        "status_generated": "lifecycle",
        "context_arrived": "lifecycle",
        # Artifact / artifact hooks
        "artifact_modified": "artifact",
        # Traceability / gaps
        "gaps_validated": "traceability",
        # Checkpoints / reviews / releases
        "checkpoint_created": "checkpoint",
        "review_completed": "review",
        "release_created": "release",
        # F_D / F_P failures (REQ-ROBUST-007)
        "fp_failure": "failure",
        "command_error": "failure",
        # Saga compensation (REQ-EVENT-004)
        "compensation_triggered": "failure",
        "compensation_completed": "convergence",
        # Health
        "health_checked": "health",
    }

    if event_type:
        return signal_map.get(event_type, "unknown")

    # Fallback: raw OL event with no sdlc:event_type facet — use top-level eventType
    ol_type = event.get("eventType", "")
    ol_fallback = {
        "START": "iteration",
        "COMPLETE": "convergence",
        "FAIL": "failure",
        "ABORT": "iteration",
        "OTHER": "lifecycle",
    }
    return ol_fallback.get(ol_type, "unknown")
