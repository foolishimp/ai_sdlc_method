# Implements: REQ-F-PARSE-004, REQ-F-EVSCHEMA-001, REQ-F-IENG-001, REQ-F-EXEC-001
"""Parse .ai-workspace/events/events.jsonl into typed Event models using OpenLineage v2 schema."""

import dataclasses
import json
import logging
import re as _re
from datetime import datetime, timezone
from pathlib import Path

from genesis_monitor.models.events import (
    EVENT_TYPE_MAP,
    Event,
)

logger = logging.getLogger(__name__)


def parse_events(workspace: Path, max_events: int = 100000) -> list[Event]:
    """Parse the append-only event log.

    Handles two formats:
    - OL-format: has ``eventType`` key (emitted by engine via ol_event.py)
    - Flat-format: has ``event_type`` key (emitted by methodology commands)

    Both are accepted; flat-format events are parsed via ``_parse_flat()``.
    """
    events_path = workspace / "events" / "events.jsonl"
    if not events_path.exists():
        return []

    events: list[Event] = []
    try:
        lines = events_path.read_text(encoding="utf-8").strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "eventType" in data:
                    events.append(_parse_one(data))
                elif "event_type" in data:
                    events.append(_parse_flat(data))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []

    return events


def _parse_one(data: dict) -> Event:
    """Dispatch to typed event using ADR-S-011 OpenLineage facets."""

    ol_type = data.get("eventType")
    run_facets = data.get("run", {}).get("facets", {})

    def _get_facet(colon_name: str) -> dict:
        return run_facets.get(colon_name) or run_facets.get(colon_name.replace(":", "_")) or {}

    req_facet = _get_facet("sdlc:req_keys")
    type_facet = _get_facet("sdlc:event_type")
    delta_facet = _get_facet("sdlc:delta")

    # Determine methodology event type
    event_type = type_facet.get("type", "unknown")
    # Normalize CamelCase → snake_case: "IterationCompleted" → "iteration_completed"
    if event_type and event_type[0].isupper():
        event_type = _re.sub(r"(?<!^)(?=[A-Z])", "_", event_type).lower()
    # OL eventType fallback — only fires when sdlc:event_type facet is absent/unknown
    if event_type == "unknown":
        if ol_type == "START":
            event_type = "edge_started"
        elif ol_type == "COMPLETE":
            event_type = "edge_converged"
        elif ol_type == "ABORT":
            event_type = "transaction_aborted"
        elif ol_type == "FAIL":
            event_type = "command_error"

    timestamp = _parse_timestamp(data.get("eventTime", ""))
    project = data.get("_metadata", {}).get("project", "")
    if not project:
        ns = data.get("job", {}).get("namespace", "")
        if ns.startswith("aisdlc://"):
            project = ns[len("aisdlc://"):]

    project = _infer_tenant(project, data)

    base_kwargs = {
        "timestamp": timestamp,
        "event_type": event_type,
        "project": project,
        "data": data,
    }

    cls = EVENT_TYPE_MAP.get(event_type)
    if cls is None:
        return Event(**base_kwargs)

    typed_kwargs = dict(base_kwargs)
    field_names = {f.name for f in dataclasses.fields(cls)}

    if "feature" in field_names:
        typed_kwargs["feature"] = req_facet.get("feature_id", "")
    if "edge" in field_names:
        edge = req_facet.get("edge", "")
        if not edge and ol_type in ("START", "COMPLETE", "ABORT"):
            edge = data.get("job", {}).get("name", "")
        typed_kwargs["edge"] = edge
    if "delta" in field_names:
        annotation = delta_facet.get("annotation")
        d = delta_facet.get("delta")
        if d is None: d = delta_facet.get("value")
        if annotation and d == 0: d = annotation
        typed_kwargs["delta"] = d

    orig = data.get("_metadata", {}).get("original_data", {})
    for f in dataclasses.fields(cls):
        if f.name in typed_kwargs: continue
        if f.name in orig: typed_kwargs[f.name] = orig[f.name]

    # ── FeatureSpawnedEvent fallbacks ────────────────────────────────────────
    # Newer OL-wrapped feature_spawned events store the child in orig["feature"]
    # and the parent in orig["data"]["parent"] rather than parent_vector/child_vector.
    if event_type == "feature_spawned":
        nested_data = orig.get("data") or {}
        if not typed_kwargs.get("child_vector"):
            typed_kwargs["child_vector"] = (
                orig.get("feature") or req_facet.get("feature_id") or ""
            )
        if not typed_kwargs.get("parent_vector"):
            typed_kwargs["parent_vector"] = (
                nested_data.get("parent") or orig.get("parent") or ""
            )
        if not typed_kwargs.get("reason"):
            typed_kwargs["reason"] = (
                nested_data.get("reason") or orig.get("reason") or ""
            )

    ev = cls(**typed_kwargs)
    _infer_executor(ev, data, is_ol=True)
    return ev


def _parse_flat(data: dict) -> Event:
    """Parse a flat-format event (has ``event_type`` but no ``eventType``).

    Flat events are emitted directly by methodology commands (gen-iterate,
    gen-gaps, gen-checkpoint, etc.) and use top-level JSON keys rather than
    OpenLineage facets.
    """
    event_type = data.get("event_type", "unknown")
    timestamp = _parse_timestamp(data.get("timestamp", ""))
    project = data.get("project", "")

    base_kwargs = {
        "timestamp": timestamp,
        "event_type": event_type,
        "project": project,
        "data": data,
    }

    cls = EVENT_TYPE_MAP.get(event_type)
    if cls is None:
        return Event(**base_kwargs)

    typed_kwargs = dict(base_kwargs)
    field_names = {f.name for f in dataclasses.fields(cls)}

    # Map well-known flat fields
    if "feature" in field_names:
        typed_kwargs["feature"] = data.get("feature", "")
    if "edge" in field_names:
        typed_kwargs["edge"] = data.get("edge", "")
    if "delta" in field_names:
        typed_kwargs["delta"] = data.get("delta")
    if "iteration" in field_names:
        typed_kwargs["iteration"] = data.get("iteration", 0)

    # Map any remaining typed fields from top-level data dict or nested data sub-dict
    nested = data.get("data") or {}
    for f in dataclasses.fields(cls):
        if f.name in typed_kwargs:
            continue
        if f.name in data:
            typed_kwargs[f.name] = data[f.name]
        elif f.name in nested:
            typed_kwargs[f.name] = nested[f.name]

    ev = cls(**typed_kwargs)
    _infer_executor(ev, data, is_ol=False)
    return ev


def _infer_executor(ev: "Event", raw: dict, *, is_ol: bool) -> None:
    """ADR-009: Set executor and emission on the event via inference rules.

    Explicit fields in raw data always win. Inference fires only when fields are absent.
    """
    # Explicit values take precedence
    explicit_executor = raw.get("executor", "") or raw.get("data", {}).get("executor", "") if isinstance(raw.get("data"), dict) else raw.get("executor", "")
    explicit_emission = raw.get("emission", "") or raw.get("data", {}).get("emission", "") if isinstance(raw.get("data"), dict) else raw.get("emission", "")

    ev.executor = explicit_executor if explicit_executor else ("engine" if is_ol else "claude")
    ev.emission = explicit_emission if explicit_emission else "live"


def _parse_timestamp(ts: str) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    try:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        # Normalise to UTC-aware so all timestamps are comparable
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


_REFLEX_LOG_TYPES = frozenset({
    "iteration_completed", "edge_converged", "evaluator_ran", "telemetry_signal_emitted",
    "edge_started", "checkpoint_created", "edge_released", "interoceptive_signal",
    "evaluator_detail", "command_error", "health_checked", "artifact_modified",
    "manual_commit", "transaction_aborted",
})

_SPEC_EVENT_LOG_TYPES = frozenset({
    "spec_modified", "feature_proposal", "feature_spawned", "feature_folded_back",
    "finding_raised", "project_initialized", "gaps_validated", "release_created",
    "exteroceptive_signal", "affect_triage", "encoding_escalated",
})

_ESCALATE_TYPES = frozenset({
    "intent_raised", "convergence_escalated", "review_completed", "claim_rejected",
    "claim_expired", "iteration_abandoned",
})


def classify_intent_engine_output(event_type: str) -> str:
    if event_type in _REFLEX_LOG_TYPES: return "reflex.log"
    if event_type in _SPEC_EVENT_LOG_TYPES: return "specEventLog"
    if event_type in _ESCALATE_TYPES: return "escalate"
    return "unclassified"


def _extract_file_path(data: dict) -> str:
    fp = data.get("_metadata", {}).get("original_data", {}).get("file_path", "")
    if fp: return fp
    fp = data.get("_metadata", {}).get("original_data", {}).get("data", {}).get("file", "")
    if fp: return fp
    outputs = data.get("outputs", [])
    if outputs and isinstance(outputs[0], dict):
        name = outputs[0].get("name", "")
        if name.startswith("file://"):
            parts = name.replace("file://", "").lstrip("/").split("/")
            for i, p in enumerate(parts):
                if p.startswith("imp_") or p == "specification": return "/".join(parts[i:])
        return name
    return ""


def _infer_tenant(project: str, data: dict) -> str:
    if project.startswith("imp_") or project == "specification": return project
    fp = _extract_file_path(data)
    if not fp: return project
    first = fp.split("/")[0]
    if first.startswith("imp_") or first == "specification": return first
    return project
