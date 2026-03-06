# ADR-025: Pragmatic Exception — Working Tree as Materialised Projection

**Status**: Accepted
**Date**: 2026-03-06
**Deciders**: Methodology Author
**Requirements**: REQ-EVENT-001, REQ-EVENT-002
**Addresses**: ADR-S-012 (Event Stream as Foundational Medium) — implementation gap
**Extends**: ADR-021 (Dual-Mode Traverse), ADR-022 (Instance Graph from Events)

---

## Context

ADR-S-012 mandates the following at spec level:

```
iterate(Asset<Tn>, Context[], Evaluators) → Event+
```

Assets are projections of the event stream. `iterate()` returns events; the engine applies them to the stream; `Asset<Tn+1>` is derived by replaying the stream to position n+1. State is never stored directly — it is always derived on demand.

### Current Implementation

The Claude Code engine (`engine.py:iterate_edge()`) does not satisfy this contract. The current signature is:

```python
def iterate_edge(edge: str, feature: str, asset_content: str, ...) -> IterationResult
```

`asset_content` is a string — the raw content of the asset file passed in. `iterate_edge()` reads and writes the filesystem directly. Events are emitted to `events.jsonl` as side effects, not as the return value of `iterate()`. The working tree (local files) is the primary state representation, not a derived projection.

This diverges from ADR-S-012 in two ways:

1. **Return type mismatch**: `IterationResult` is not `Event+`. The engine returns a structured summary of the iteration, not a list of events for the caller to apply.

2. **Mutable working tree**: The engine writes files as primary state. The event log is a secondary record, not the source of truth. Replaying `events.jsonl` cannot reconstruct asset content — the content lives only in the files.

### Why This Divergence Exists

ADR-S-012 was accepted on 2026-03-04. The engine was substantially complete by then. Retrofitting `iterate()` to return `Event+` requires:

1. Changing the engine's return type and all callers
2. Implementing a projection layer that reconstructs asset content from events (or storing content in events — `asset_content: str` embedded in the event payload)
3. Implementing an event-application step between `iterate()` and the next read
4. Aligning the working tree sync with the projection (so editors and tools still see current files)

This is a meaningful refactor. The current implementation is working — 760 tests pass, dogfood runs complete, the event log is emitted correctly. Breaking the engine to satisfy a formal model purity constraint at this stage would be destructive to working software.

### The Pragmatic Mapping

The current implementation satisfies the *spirit* of ADR-S-012 while diverging from the *letter*:

| ADR-S-012 requirement | Current implementation | Conformant? |
|----------------------|----------------------|-------------|
| Events appended on every iteration | ✓ `events.jsonl` receives one event per `iterate_edge()` call | Yes |
| Event stream is append-only | ✓ events.jsonl is never modified, only appended | Yes |
| Events carry `event_type`, `timestamp`, `feature`, `edge`, `iteration` | ✓ emitted by `fd_emit.py` and `ol_event.py` | Yes |
| Asset state derivable from events | ✗ `asset_content` is not stored in events | No |
| `iterate()` returns `Event+` | ✗ returns `IterationResult` | No |
| Projection determinism, completeness, isolation | ✗ completeness violated — asset content not in stream | No |

The working tree (local files) acts as an **implicit materialised projection** — a cache that is kept in sync with each write. This satisfies projection performance at the cost of formal spec compliance.

---

## Decision

### Formal Exception

The Claude Code engine (`imp_claude/`) is granted a formal exception from the full ADR-S-012 conformance requirement for v3.x:

**Exception**: `iterate_edge()` MAY continue to use `asset_content: str` as input and `IterationResult` as output. The working tree MAY serve as the primary state representation. Events MUST continue to be emitted as side effects to `events.jsonl` with all required fields except `asset_content`.

This exception applies to the **engine execution path** only. Event emission, the event schema, and the event log remain mandatory and are not excepted.

### Migration Path (v4.x)

Full ADR-S-012 conformance is deferred to a future major version when the engine refactor is scheduled deliberately, not reactively. The migration has three steps:

**Step 1 — Asset content in events (prerequisite)**:
Embed `asset_content: str` in `IterationCompleted` events. This is additive — no existing consumers break. Events become self-sufficient for reconstruction. `events.jsonl` becomes the source of truth for asset content.

**Step 2 — Projection layer**:
Add a `project(events, feature, edge) → str` function that replays the event stream and returns the current asset content for a given feature+edge. This replaces the direct filesystem read in `iterate_edge()`.

**Step 3 — Signature change**:
Change `iterate_edge()` to accept `Asset<Tn>` (the projected asset) and return `List[Event]`. The engine applies returned events to the stream. The working tree is updated as a derived side effect of event application, not as primary state.

Steps 1 and 2 are independently deployable without breaking the API. Step 3 is the breaking change that achieves full ADR-S-012 conformance.

### Immediate Action (v3.x)

No code change in this ADR. The exception is a design record, not a task.

One partial step is within scope for v3.x: **Step 1 (asset content in events)** can be added to `fd_emit.py` without touching the engine signature. The `asset_content` field would be optional in v3.x (for event log enrichment) and mandatory in v4.x (for projection). This is tracked in REQ-F-EVENT-001.

---

## Consequences

### Positive
- No disruption to working engine — 760 tests remain green
- Exception is documented and bounded — no ambiguity about scope
- Migration path is concrete and incremental — each step is independently shippable
- v3.x can continue delivering features against the working engine

### Negative
- `events.jsonl` cannot reconstruct asset content without the working tree — a partial conformance failure against ADR-S-012
- Multi-instance or cloud deployments cannot replay asset state from events alone — this bounds the deployment model to single-machine for v3.x
- The exception must be re-evaluated at v4.x planning — it is not permanent

### Neutral
- The Gemini and Bedrock implementations are not affected — they own their own event emission
- ADR-S-012 remains accepted at spec level — the exception is implementation-local to `imp_claude/`

---

## References

- ADR-S-012: Event Stream as Foundational Medium (spec-level decision being excepted)
- ADR-S-011: OpenLineage Unified Metadata Standard (event schema)
- ADR-021: Dual-Mode Traverse (engine architecture)
- ADR-022: Instance Graph from Events (projection layer for display, not execution)
- REQ-EVENT-001: Event Stream & Projections feature vector (tracks Step 1 migration)
- `imp_claude/code/genesis/engine.py:iterate_edge()` — current signature
- `imp_claude/code/genesis/fd_emit.py` — event emission (Step 1 target)
- `imp_claude/code/genesis/ol_event.py` — OpenLineage event schema
