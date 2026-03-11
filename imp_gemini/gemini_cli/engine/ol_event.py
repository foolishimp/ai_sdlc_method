# Implements: REQ-EVENT-001 (OpenLineage event construction), REQ-EVENT-003 (Required Event Taxonomy), REQ-EVENT-004 (Saga Invariant), REQ-EVOL-003 (feature_proposal event), REQ-EVOL-004 (spec_modified event), REQ-COORD-002 (Multi-Agent Coordination), ADR-S-011, ADR-S-012
# Implements: REQ-EVENT-002 (Projection Contract \u2014 instance_id isolation, deterministic event construction)
# Implements: REQ-LIFE-003 (Feedback Loop Closure), REQ-LIFE-004 (Feature Lineage in Telemetry)
# Implements: REQ-LIFE-005 (Intent Events as First-Class Objects)
# Implements: REQ-EVENT-005 (Executor Attribution Fields \u2014 actor/causation_id on every event; executor/emission optional fields per spec)
"""
OpenLineage event constructor \u2014 builds spec-compliant RunEvents.

Every event carries four universal fields (ADR-S-012):
  instance_id    \u2014 workflow instance scope
  actor          \u2014 who/what caused the event
  causation_id   \u2014 runId of the immediate parent event (ParentRunFacet)
  correlation_id \u2014 runId of the root event in the causal chain

Root events (no triggering parent) set causation_id = correlation_id = own runId.
"""

import argparse
import fcntl
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

PRODUCER = "https://github.com/foolishimp/ai_sdlc_method"
SCHEMA_URL = "https://openlineage.io/spec/1-0-5/OpenLineage.json"
FACET_SCHEMA_BASE = "https://github.com/foolishimp/ai_sdlc_method/spec/facets"

# \u2500\u2500 Multi-tenancy: map file path prefix \u2192 design tenant (REQ-TOOL-012) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_TENANT_PREFIXES = ("imp_claude", "imp_gemini", "imp_codex", "imp_bedrock")


from typing import Any, Dict, List, Optional, Union

def tenant_from_path(file_path: Union[str, Path]) -> Optional[str]:
    """Return the design tenant name from a relative file path, or None."""
    first = Path(file_path).parts[0] if file_path else ""
    if first in _TENANT_PREFIXES or first == "specification":
        return first
    return None


# ADR-S-011: semantic event type \u2192 OL eventType
_OL_EVENT_TYPE = {
    # Core iteration lifecycle (REQ-EVENT-003)
    "IterationStarted": "START",
    "IterationCompleted": "OTHER",  # non-terminal \u2014 convergence not yet declared
    "IterationFailed": "FAIL",
    "IterationAbandoned": "ABORT",
    # Convergence events (REQ-EVENT-003)
    "EvaluatorVoted": "OTHER",  # one evaluator cast a vote \u2014 intermediate
    "ConsensusReached": "COMPLETE",  # all required evaluators passed \u2014 terminal
    "ConsensusFailed": "FAIL",
    "ConvergenceAchieved": "COMPLETE",  # alias: full edge convergence
    # Context events (REQ-EVENT-003)
    "ContextArrived": "OTHER",  # new context pushed into iteration
    # Transition gate events
    "TransitionAuthorized": "COMPLETE",  # gate passed \u2014 edge may proceed
    "TransitionDenied": "FAIL",  # gate denied \u2014 edge blocked
    # Saga compensation (REQ-EVENT-004)
    "CompensationTriggered": "OTHER",  # failure on B\u2192C \u2192 compensate A\u2192B
    "CompensationCompleted": "COMPLETE",  # compensation done \u2014 chain restored
    # Consciousness loop Stage 2+3 (ADR-011, ADR-S-008)
    "FeatureProposed": "OTHER",  # intent_raised \u2192 affect triage \u2192 draft proposal
    "FeatureApproved": "COMPLETE",  # human approves proposal \u2192 inflates workspace
    "FeatureDismissed": "OTHER",  # human dismisses proposal \u2192 archived
    # Spec evolution (REQ-EVOL-004, ADR-S-010)
    "SpecModified": "COMPLETE",  # specification/ file changed \u2014 causal chain recorded
    # Engine lifecycle events (REQ-EVENT-003)
    "EdgeStarted": "OTHER",  # edge traversal begins
    "EdgeConverged": "COMPLETE",  # edge fully converged \u2014 terminal
    "FpFailure": "OTHER",  # F_P actor failed to converge (REQ-ROBUST-007)
    "EvaluatorDetail": "OTHER",  # per-check evaluator result (REQ-ROBUST-007)
    "CommandError": "OTHER",  # engine CLI command error (REQ-SUPV-003)
    # Spawn lifecycle
    "SpawnCreated": "OTHER",  # child vector created
    "SpawnFoldedBack": "COMPLETE",  # child results folded back to parent
    # Multi-agent coordination (ADR-013, REQ-COORD-002)
    "EdgeClaimed": "OTHER",  # agent claims a feature+edge \u2014 pending serialiser confirmation
    "ClaimRejected": "FAIL",  # serialiser rejects claim (conflict or role violation)
    "ClaimExpired": "OTHER",  # stale claim detected (no follow-up within timeout)
    "EdgeReleased": "OTHER",  # agent voluntarily releases a claim
    "ConvergenceEscalated": "OTHER",  # convergence outside agent role authority \u2192 human gate
}


def make_ol_event(
    event_type: str,
    job_name: str,
    project: str,
    instance_id: str,
    actor: str,
    causation_id: str | None = None,
    correlation_id: str | None = None,
    payload: dict | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    project_root: str | None = None,
) -> dict:
    """Construct an OpenLineage RunEvent dict (ADR-S-011, ADR-S-012)."""
    run_id = str(uuid.uuid4())
    root = project_root or str(Path.cwd())
    namespace = f"aisdlc://{project}"
    file_ns = f"file://{root}"

    # Root events are self-referential
    causation_id = causation_id or run_id
    correlation_id = correlation_id or run_id

    ol_type = _OL_EVENT_TYPE.get(event_type, "OTHER")

    # Universal facets
    run_facets: dict = {
        "sdlc:universal": {
            "_producer": PRODUCER,
            "_schemaURL": f"{FACET_SCHEMA_BASE}/sdlc_universal.json",
            "instance_id": instance_id,
            "actor": actor,
            "causation_id": causation_id,
            "correlation_id": correlation_id,
        },
        "parent": {
            "_producer": PRODUCER,
            "_schemaURL": "https://openlineage.io/spec/facets/ParentRunFacet.json",
            "run": {"runId": causation_id},
            "job": {"namespace": namespace, "name": job_name},
        },
    }

    # Semantic type facet
    if payload or ol_type == "OTHER":
        run_facets["sdlc:event_type"] = {
            "_producer": PRODUCER,
            "_schemaURL": f"{FACET_SCHEMA_BASE}/sdlc_event_type.json",
            "type": event_type,
        }

    # Payload facet
    if payload:
        run_facets["sdlc:payload"] = {
            "_producer": PRODUCER,
            "_schemaURL": f"{FACET_SCHEMA_BASE}/sdlc_payload.json",
            **payload,
        }

    def _dataset(path: str) -> dict:
        return {"namespace": file_ns, "name": path, "facets": {}}

    return {
        "eventType": ol_type,
        "eventTime": datetime.now(timezone.utc).isoformat(),
        "run": {"runId": run_id, "facets": run_facets},
        "job": {"namespace": namespace, "name": job_name, "facets": {}},
        "inputs": [_dataset(p) for p in (inputs or [])],
        "outputs": [_dataset(p) for p in (outputs or [])],
        "producer": PRODUCER,
        "schemaURL": SCHEMA_URL,
    }


def emit_ol_event(events_path: Path, event: dict) -> str:
    """Append an OL event dict to events.jsonl. Returns the runId."""
    events_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, separators=(",", ":")) + "\n"

    with open(events_path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return event["run"]["runId"]


import re as _re


def normalize_event(raw: dict) -> dict:
    """Normalize an OL RunEvent to flat event format, or pass through flat events."""
    if "event_type" in raw:
        return raw  # Already flat format

    facets = raw.get("run", {}).get("facets", {})
    event_type_facet = facets.get("sdlc:event_type", {})
    if not event_type_facet:
        # Fallback for old events or non-OL
        return raw

    semantic_type = event_type_facet.get("type", "")
    # CamelCase \u2192 snake_case: "IterationCompleted" \u2192 "iteration_completed"
    event_type = _re.sub(r"(?<!^)(?=[A-Z])", "_", semantic_type).lower()

    # Project from job namespace: "aisdlc://my-project" \u2192 "my-project"
    namespace = raw.get("job", {}).get("namespace", "")
    project = namespace.removeprefix("aisdlc://")

    # Payload fields (skip internal _producer/_schemaURL keys)
    payload_facet = facets.get("sdlc:payload", {})

    flat: dict = {
        "event_type": event_type,
        "timestamp": raw.get("eventTime", ""),
        "project": project,
    }
    flat.update({k: v for k, v in payload_facet.items() if not k.startswith("_")})
    return flat


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------


def iteration_started(project, instance_id, actor, edge, context_refs=None, payload=None, **kw) -> dict:
    p = {"edge": edge, "context_refs": context_refs or []}
    if payload: p.update(payload)
    return make_ol_event(
        "IterationStarted", edge, project, instance_id, actor,
        payload=p, **kw
    )


def iteration_completed(project, instance_id, actor, edge, delta, payload=None, **kw) -> dict:
    p = {"edge": edge, "delta": delta}
    if payload: p.update(payload)
    return make_ol_event(
        "IterationCompleted", edge, project, instance_id, actor,
        payload=p, **kw
    )


def iteration_failed(project, instance_id, actor, edge, reason, payload=None, **kw) -> dict:
    p = {"edge": edge, "reason": reason}
    if payload: p.update(payload)
    return make_ol_event(
        "IterationFailed", edge, project, instance_id, actor,
        payload=p, **kw
    )


def evaluator_voted(project, instance_id, actor, evaluator_type, result, evidence, **kw) -> dict:
    return make_ol_event(
        "EvaluatorVoted", "EVALUATOR", project, instance_id, actor,
        payload={"evaluator_type": evaluator_type, "result": result, "evidence": evidence},
        **kw
    )


def consensus_reached(project, instance_id, actor, edge, evaluator_count, **kw) -> dict:
    return make_ol_event(
        "ConsensusReached", edge, project, instance_id, actor,
        payload={"edge": edge, "evaluator_count": evaluator_count},
        **kw
    )


def convergence_achieved(project, instance_id, actor, edge, delta, payload=None, **kw) -> dict:
    p = {"edge": edge, "delta": delta}
    if payload: p.update(payload)
    return make_ol_event(
        "ConvergenceAchieved", edge, project, instance_id, actor,
        payload=p, **kw
    )


def compensation_triggered(project, instance_id, actor, failed_edge, target_edge, **kw) -> dict:
    return make_ol_event(
        "CompensationTriggered", f"COMPENSATE:{target_edge}", project, instance_id, actor,
        payload={"failed_edge": failed_edge, "target_edge": target_edge},
        **kw
    )


def compensation_completed(project, instance_id, actor, target_edge, restored_projection_hash, **kw) -> dict:
    return make_ol_event(
        "CompensationCompleted", f"COMPENSATE:{target_edge}", project, instance_id, actor,
        payload={"target_edge": target_edge, "restored_projection_hash": restored_projection_hash},
        **kw
    )


def context_arrived(project, instance_id, actor, source_type, payload_ref, **kw) -> dict:
    return make_ol_event(
        "ContextArrived", "CONTEXT", project, instance_id, actor,
        payload={"source_type": source_type, "payload_ref": payload_ref}, **kw
    )


def edge_started(project, instance_id, actor, edge, **kw) -> dict:
    return make_ol_event("EdgeStarted", edge, project, instance_id, actor, **kw)


def edge_converged(project, instance_id, actor, edge, **kw) -> dict:
    return make_ol_event("EdgeConverged", edge, project, instance_id, actor, **kw)


def spawn_created(project, instance_id, actor, child_feature, parent_feature, **kw) -> dict:
    return make_ol_event(
        "SpawnCreated", f"SPAWN:{child_feature}", project, instance_id, actor,
        payload={"child_feature": child_feature, "parent_feature": parent_feature}, **kw
    )


def spawn_folded_back(project, instance_id, actor, child_feature, parent_feature, **kw) -> dict:
    return make_ol_event(
        "SpawnFoldedBack", f"SPAWN:{child_feature}", project, instance_id, actor,
        payload={"child_feature": child_feature, "parent_feature": parent_feature}, **kw
    )


def transition_authorized(project, instance_id, actor, edge, permissions, **kw) -> dict:
    return make_ol_event(
        "TransitionAuthorized", edge, project, instance_id, actor,
        payload={"edge": edge, "permissions": permissions}, **kw
    )


def transition_denied(project, instance_id, actor, edge, reason, **kw) -> dict:
    return make_ol_event(
        "TransitionDenied", edge, project, instance_id, actor,
        payload={"edge": edge, "reason": reason}, **kw
    )


def feature_proposed(project, instance_id, actor, feature, description, **kw) -> dict:
    return make_ol_event(
        "FeatureProposed", f"PROPOSE:{feature}", project, instance_id, actor,
        payload={"feature": feature, "description": description}, **kw
    )


def feature_approved(project, instance_id, actor, feature, **kw) -> dict:
    return make_ol_event(
        "FeatureApproved", f"APPROVE:{feature}", project, instance_id, actor,
        payload={"feature": feature}, **kw
    )


def feature_dismissed(project, instance_id, actor, feature, reason, **kw) -> dict:
    return make_ol_event(
        "FeatureDismissed", f"DISMISS:{feature}", project, instance_id, actor,
        payload={"feature": feature, "reason": reason}, **kw
    )


def spec_modified(project, instance_id, actor, file, what_changed, previous_hash, new_hash, trigger_event_id, trigger_type, **kw) -> dict:
    return make_ol_event(
        "SpecModified", f"SPEC_MODIFIED:{file}", project, instance_id, actor,
        payload={
            "file": file,
            "what_changed": what_changed,
            "previous_hash": previous_hash,
            "new_hash": new_hash,
            "trigger_event_id": trigger_event_id,
            "trigger_type": trigger_type
        }, **kw
    )
