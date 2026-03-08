# Implements: REQ-F-CONSC-001, REQ-F-CONSC-002, REQ-F-CONSC-003
"""Build consciousness timeline from deliberative events."""

from __future__ import annotations

from genesis_monitor.models.events import (
    ConvergenceEscalatedEvent,
    Event,
    FeatureSpawnedEvent,
    FindingRaisedEvent,
    IntentRaisedEvent,
    ReleaseCreatedEvent,
    ReviewCompletedEvent,
    SpecModifiedEvent,
)

# Event types that represent conscious/deliberative activity
CONSCIOUSNESS_EVENT_TYPES = frozenset({
    "intent_raised",
    "spec_modified",
    "finding_raised",
    "feature_spawned",
    "feature_folded_back",
    "release_created",
    # v2.8 additions
    "convergence_escalated",
    "review_completed",
    # gen-spawn flat format (equiv to feature_spawned, different schema)
    "spawn_created",
})


def build_consciousness_timeline(events: list[Event]) -> list[dict]:
    """Extract conscious/deliberative events into a chronological timeline.

    Filters to intent chains, spec modifications, findings, and spawn events.
    Returns a list of dicts sorted by timestamp with event-type-specific fields.
    """
    timeline = []

    for e in events:
        if e.event_type not in CONSCIOUSNESS_EVENT_TYPES:
            continue

        entry: dict = {
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "project": e.project,
        }

        if isinstance(e, IntentRaisedEvent):
            entry["trigger"] = e.trigger
            entry["signal_source"] = e.signal_source
            # Extract richer metadata from raw event data
            raw = e.data
            orig = raw.get("_metadata", {}).get("original_data") or raw
            nested = orig.get("data") or {} if isinstance(orig, dict) else {}
            entry["intent_id"] = (
                nested.get("intent_id") or orig.get("intent_id") or ""
                if isinstance(orig, dict) else ""
            )
            entry["description"] = (
                nested.get("description") or orig.get("description")
                or nested.get("delta") or ""
                if isinstance(orig, dict) else ""
            )
            req_keys = (
                orig.get("affected_req_keys") or nested.get("affected_req_keys") or []
                if isinstance(orig, dict) else []
            )
            entry["affected_req_keys"] = req_keys[:6]
            # Skip entries with no meaningful content (blank OL-wrapped events)
            if not any([e.trigger, entry["intent_id"], entry["description"], req_keys]):
                continue
        elif isinstance(e, SpecModifiedEvent):
            entry["trigger_intent"] = e.trigger_intent
            if e.delta:
                entry["delta"] = e.delta
            else:
                # Format B: delta stored in data.what_changed + data.file
                raw = e.data
                orig = raw.get("_metadata", {}).get("original_data") or raw
                nested = orig.get("data") or {} if isinstance(orig, dict) else {}
                what = nested.get("what_changed") or orig.get("what_changed") or ""
                file_path = nested.get("file") or orig.get("file_path") or ""
                if what:
                    entry["delta"] = what
                    entry["file_path"] = file_path
                    if not entry["trigger_intent"]:
                        entry["trigger_intent"] = (
                            nested.get("trigger_event_id") or orig.get("trigger_event_id") or ""
                        )
                else:
                    entry["delta"] = ""
        elif isinstance(e, FindingRaisedEvent):
            entry["finding_type"] = e.finding_type
            entry["description"] = e.description
        elif isinstance(e, FeatureSpawnedEvent):
            entry["parent_vector"] = e.parent_vector
            entry["child_vector"] = e.child_vector
            entry["reason"] = e.reason
        elif isinstance(e, ConvergenceEscalatedEvent):
            entry["edge"] = e.edge
            entry["reason"] = e.reason
            entry["escalated_to"] = e.escalated_to
        elif isinstance(e, ReviewCompletedEvent):
            entry["edge"] = e.edge
            entry["feature"] = e.feature
            entry["reviewer"] = e.reviewer
            entry["outcome"] = e.outcome
        elif isinstance(e, ReleaseCreatedEvent):
            entry["version"] = e.version
            entry["features_included"] = e.features_included
        elif e.event_type == "spawn_created":
            # gen-spawn flat format: feature=child_id, data.intent, data.trigger, data.title
            d = e.data
            nested = d.get("data") or {}
            entry["child_vector"] = d.get("feature") or ""
            entry["parent_vector"] = nested.get("parent") or d.get("parent") or ""
            entry["reason"] = nested.get("trigger") or nested.get("reason") or ""
            entry["title"] = nested.get("title") or ""
            # Normalise display event_type so template re-uses feature_spawned branch
            entry["event_type"] = "feature_spawned"

        timeline.append(entry)

    timeline.sort(key=lambda x: x["timestamp"])

    # Compact intent_raised events:
    # 1. Deduplicate by intent_id — keep latest occurrence per named intent
    # 2. Collapse consecutive unnamed events with the same trigger into one with a count
    seen_intent_ids: set[str] = set()
    deduped = []
    for entry in reversed(timeline):
        if entry["event_type"] == "intent_raised":
            iid = entry.get("intent_id", "")
            if iid:
                if iid in seen_intent_ids:
                    continue
                seen_intent_ids.add(iid)
            else:
                # For unnamed entries, collapse consecutive same-trigger events
                trigger = entry.get("trigger", "")
                desc_key = entry.get("description", "")[:40]
                if (deduped and deduped[-1]["event_type"] == "intent_raised"
                        and not deduped[-1].get("intent_id")
                        and deduped[-1].get("trigger") == trigger
                        and deduped[-1].get("description", "")[:40] == desc_key):
                    deduped[-1]["_count"] = deduped[-1].get("_count", 1) + 1
                    continue
        deduped.append(entry)
    deduped.reverse()

    return deduped
