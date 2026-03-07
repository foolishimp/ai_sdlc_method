"""OpenLineage event append/replay helpers for the Codex runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid


PRODUCER = "https://github.com/foolishimp/ai_sdlc_method/imp_codex"
RUN_EVENT_SCHEMA = "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
UNIVERSAL_SCHEMA = "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_universal.json"
EVENT_TYPE_SCHEMA = "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_event_type.json"
PAYLOAD_SCHEMA = "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_payload.json"
PARENT_SCHEMA = "https://openlineage.io/spec/facets/ParentRunFacet.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def semantic_to_ol_type(semantic_type: str) -> str:
    mapping = {
        "IterationStarted": "START",
        "IterationCompleted": "OTHER",
        "ConvergenceAchieved": "COMPLETE",
        "IterationFailed": "FAIL",
        "IterationAbandoned": "ABORT",
    }
    return mapping.get(semantic_type, "OTHER")


def _snake_to_pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def normalize_semantic_type(raw: str | None, ol_type: str | None = None) -> str:
    if raw:
        if "_" in raw:
            aliases = {
                "edge_started": "IterationStarted",
                "iteration_started": "IterationStarted",
                "iteration_completed": "IterationCompleted",
                "edge_converged": "ConvergenceAchieved",
                "feature_converged": "ConvergenceAchieved",
            }
            return aliases.get(raw, _snake_to_pascal(raw))
        return raw
    if ol_type == "START":
        return "IterationStarted"
    if ol_type == "COMPLETE":
        return "ConvergenceAchieved"
    if ol_type == "FAIL":
        return "IterationFailed"
    if ol_type == "ABORT":
        return "IterationAbandoned"
    return "Other"


@dataclass(frozen=True)
class NormalizedEvent:
    """Runtime-friendly view of an event log row."""

    raw: dict
    semantic_type: str
    event_time: str
    project: str
    feature: str | None
    edge: str | None
    iteration: int | None
    delta: int | None
    status: str | None


def build_run_event(
    *,
    project_name: str,
    semantic_type: str,
    actor: str,
    feature: str | None = None,
    edge: str | None = None,
    payload: dict | None = None,
    run_id: str | None = None,
    causation_id: str | None = None,
    correlation_id: str | None = None,
    parent_run_id: str | None = None,
    event_time: str | None = None,
) -> dict:
    """Construct a canonical OpenLineage RunEvent with SDLC facets."""

    payload = dict(payload or {})
    run_id = run_id or str(uuid.uuid4())
    event_time = event_time or utc_now()
    edge_name = edge or payload.get("edge") or semantic_type
    namespace = f"aisdlc://{project_name}"

    universal = {
        "_producer": PRODUCER,
        "_schemaURL": UNIVERSAL_SCHEMA,
        "instance_id": feature or edge_name,
        "actor": actor,
        "causation_id": causation_id or run_id,
        "correlation_id": correlation_id or run_id,
    }
    event_type_facet = {
        "_producer": PRODUCER,
        "_schemaURL": EVENT_TYPE_SCHEMA,
        "type": semantic_type,
    }
    payload_facet = {
        "_producer": PRODUCER,
        "_schemaURL": PAYLOAD_SCHEMA,
    }
    payload_facet.update(payload)

    facets = {
        "sdlc:universal": universal,
        "sdlc:event_type": event_type_facet,
        "sdlc:payload": payload_facet,
    }
    if parent_run_id:
        facets["parent"] = {
            "_producer": PRODUCER,
            "_schemaURL": PARENT_SCHEMA,
            "run": {"runId": parent_run_id},
            "job": {"namespace": namespace, "name": edge_name},
        }

    return {
        "eventType": semantic_to_ol_type(semantic_type),
        "eventTime": event_time,
        "producer": PRODUCER,
        "schemaURL": RUN_EVENT_SCHEMA,
        "job": {
            "namespace": namespace,
            "name": edge_name,
        },
        "run": {
            "runId": run_id,
            "facets": facets,
        },
    }


def append_run_event(
    events_file: Path,
    *,
    project_name: str,
    semantic_type: str,
    actor: str,
    feature: str | None = None,
    edge: str | None = None,
    payload: dict | None = None,
    run_id: str | None = None,
    causation_id: str | None = None,
    correlation_id: str | None = None,
    parent_run_id: str | None = None,
    event_time: str | None = None,
) -> dict:
    """Append a canonical RunEvent to the JSONL event log."""

    event = build_run_event(
        project_name=project_name,
        semantic_type=semantic_type,
        actor=actor,
        feature=feature,
        edge=edge,
        payload=payload,
        run_id=run_id,
        causation_id=causation_id,
        correlation_id=correlation_id,
        parent_run_id=parent_run_id,
        event_time=event_time,
    )
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "a") as handle:
        handle.write(json.dumps(event, sort_keys=True))
        handle.write("\n")
    return event


def normalize_event(raw: dict) -> NormalizedEvent:
    """Normalize legacy and OpenLineage event rows into one view."""

    facets = raw.get("run", {}).get("facets", {})
    payload = facets.get("sdlc:payload") or raw.get("data") or {}
    semantic_raw = (
        facets.get("sdlc:event_type", {}).get("type")
        or raw.get("event_type")
        or raw.get("_metadata", {}).get("original_data", {}).get("event_type")
    )
    semantic = normalize_semantic_type(semantic_raw, raw.get("eventType"))
    namespace = raw.get("job", {}).get("namespace", "")
    project = raw.get("project") or namespace.replace("aisdlc://", "", 1)
    iteration = payload.get("iteration")
    if iteration is None:
        iteration = raw.get("iteration")
    delta = payload.get("delta")
    if delta is None and isinstance(raw.get("data"), dict):
        delta = raw["data"].get("delta")
    status = payload.get("status")
    if status is None and isinstance(raw.get("data"), dict):
        status = raw["data"].get("status")
    return NormalizedEvent(
        raw=raw,
        semantic_type=semantic,
        event_time=raw.get("eventTime") or raw.get("timestamp") or "",
        project=project,
        feature=payload.get("feature") or raw.get("feature"),
        edge=payload.get("edge") or raw.get("edge"),
        iteration=iteration,
        delta=delta,
        status=status,
    )


def load_events(events_file: Path) -> list[NormalizedEvent]:
    """Load and normalize all event rows from a JSONL log."""

    if not events_file.exists():
        return []
    events: list[NormalizedEvent] = []
    with open(events_file) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            events.append(normalize_event(json.loads(line)))
    return events


__all__ = [
    "NormalizedEvent",
    "append_run_event",
    "build_run_event",
    "load_events",
    "normalize_event",
    "normalize_semantic_type",
    "semantic_to_ol_type",
    "utc_now",
]
