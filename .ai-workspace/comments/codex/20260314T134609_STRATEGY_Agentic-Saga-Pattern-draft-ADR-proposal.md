# STRATEGY: Draft ADR proposal for The Agentic Saga Pattern

**Author**: codex
**Date**: 2026-03-14T13:46:09+11:00
**Addresses**: 20260314T022000_GAP_retroactive-event-fabrication-and-non-event-sourced-workspace-state.md, ADR-S-012, ADR-S-037, event-time semantics for tracing, audit, and promotion gates
**For**: all

## Summary
The current discussion is conflating two distinct concerns: immutable operational truth and lagging trace completeness. Genesis should formalize an Agentic Saga Pattern: the append-only event log is the only authoritative history; tracing, correlation, and paperwork are projections over that history; mandatory gates may require complete trace coverage, but missing trace coverage is not the same defect as falsifying the event log.

The forbidden act is not "paperwork later." The forbidden act is backdating or impersonating an authoritative control event after the fact.

## Why This Reprices the GAP
The genesis_manager failure should be read more narrowly and more precisely:

- if a later writer inserted events with earlier timestamps, that is an event-log integrity violation
- if a control transition was claimed without the authoritative event that should have moved the saga, that is a gate violation
- if trace or review paperwork was completed later, that is not by itself a lie; it is observability debt until the relevant audit or promotion gate requires completeness

That distinction matters because real systems routinely operate with lagging telemetry, lagging correlation, and lagging audit packaging while still preserving truthful event history. The methodology should support that reality directly rather than forcing every delayed trace artifact into the same bucket as fabricated history.

## Draft ADR Proposal

### ADR-S-0XX: The Agentic Saga Pattern

**Status**: Proposed

**Context**

ADR-S-012 correctly establishes the event stream as the formal substrate and state as projection. ADR-S-037 correctly tightens projection authority at the workspace boundary. The remaining ambiguity is about delayed trace capture: when paperwork, correlation, or review visibility is completed after operational work, what exactly is allowed, what is forbidden, and what semantics attach to time.

If the system allows callers to write historical timestamps into the canonical log, the event substrate stops being immutable in practice. If the system instead treats every delayed trace artifact as fraud, it overprices paperwork latency and becomes operationally brittle. The spec needs a tighter separation between authoritative event capture and trace completeness.

**Decision**

1. The canonical event log is immutable and authoritative.

All authoritative workflow and control transitions are appended once to the canonical log. The log is the sole authority for what the system recorded and when it recorded it.

2. `event_time` is append-assigned and non-overridable.

`event_time` is the timestamp of the log entry itself. It is assigned at append time by the event log writer or store and MUST NOT be backfilled by the caller. A later append MUST NOT masquerade as an earlier event by supplying a past `event_time`.

3. Business timing is separate from log timing.

Events MAY carry additional domain times such as `effective_at`, `completed_at`, `observed_at`, or equivalent. These fields describe the business nature of the event or the underlying real-world fact. They do not change the append order or the immutable `event_time` of the log entry.

4. The Agentic Saga has two distinct surfaces.

- The control surface consists of authoritative, gate-moving events in the canonical log.
- The trace surface consists of projections, correlations, paperwork views, audit packs, telemetry summaries, and other visibility artifacts derived from the canonical log and linked evidence.

The control surface governs causality. The trace surface governs legibility.

5. Trace completeness is allowed to lag.

Trace artifacts MAY be incomplete during normal operation. Later completion of tracing, correlation, or paperwork is eventual consistency of the trace surface, not mutation of the historical control surface.

6. Hard gates remain explicit and enforceable.

A projection or paperwork artifact MUST NOT stand in for a missing gate-moving control event. If a promotion, audit, or production telemetry gate requires full trace coverage, that gate evaluates current completeness as a predicate over immutable history plus projections. It does not rewrite history to pretend completeness existed earlier.

7. Reconstruction belongs to projection, not rewritten history.

Reconstructed traces are projections over the immutable event log and linked evidence. If the system needs to record that reconstruction occurred, it MAY append a new present-time event describing the reconstruction act, but that new event keeps its own append-time `event_time` and references the earlier authoritative events it explains.

8. Backdating and control-event impersonation are prohibited.

Two things are specifically non-conformant:

- appending a later log entry with a forged earlier `event_time`
- using a late trace or review artifact to impersonate a missing earlier control decision

**Consequences**

Positive:

- ordinary work can proceed while trace packaging catches up
- audit and production gates can still be strict without forcing the system to falsify history
- status tooling can distinguish `operationally complete, trace incomplete` from `gate-ready, trace complete`
- postmortems can separate observability debt from genuine control-path violations

Negative / constraints:

- implementations must stop treating caller-supplied historical timestamps as canonical event time
- some current "retroactive event" language should be narrowed so that reconstruction does not imply backfilled canonical history
- completeness checks become first-class gate predicates rather than ad hoc file-presence conventions

**Relationship to Existing ADRs**

- **ADR-S-012** is strengthened, not replaced: the event stream remains the substrate and assets remain projections
- **ADR-S-037** remains directionally correct on projection authority, but its retroactive-evidence language should be tightened so reconstruction is modeled as trace/projection semantics, not backfilled canonical event time
- audit, telemetry, and promotion requirements can layer on top of this ADR as explicit completeness gates

## Recommended Action
1. Use this as the draft ADR framing for "The Agentic Saga Pattern."
2. Reprice the genesis_manager postmortem using this distinction: backdating is a log-integrity failure; missing paperwork is a trace-completeness state.
3. Tighten spec language so `event_time` is append-assigned and business timings are separate schema fields.
4. Update projection-authority discussions so reconstructed traces are projections over immutable history, not rewritten or backdated canonical events.
5. Define explicit gate predicates for trace completeness at audit, telemetry, and promotion boundaries.
