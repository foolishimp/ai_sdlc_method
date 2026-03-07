# ADR-004: Scalable Event Index — Prometheus/Loki-Inspired Architecture

**Status**: Proposed
**Date**: 2026-03-08
**Implements**: REQ-F-ELIN-001, REQ-F-EVOL-001, REQ-NFR-001
**Supersedes**: Current in-memory full-load approach (app.py lifespan)

---

## Context

The current architecture loads the entire event log into memory on startup, rebuilds all
projections synchronously on every HTTP request, and has no incremental update path.
This is acceptable for the current dogfood scale (~1500 events, 7 projects) but breaks at:
- 100k+ events per project (long-running production projects)
- 50+ projects monitored simultaneously
- Sub-second SSE push for live updates during active iteration

### Best-of-Breed Reference Architecture

Three tools inform the design:

**Prometheus** (TSDB):
- Write-ahead log (WAL) for durability
- In-memory head chunk for hot data (recent N events)
- Immutable blocks for cold data (compressed, content-addressed)
- Range queries scan only relevant blocks via metadata index
- Lesson: separate hot path (recent events) from cold path (historical)

**Loki** (log aggregation):
- Label-based inverted index: `{feature="REQ-F-AUTH-001", edge="code↔unit_tests"}` → chunk IDs
- Chunks are compressed segments of the log
- Queries are range + label filter: no full scan
- Lesson: build an inverted index on (feature, edge, event_type, project) at ingest time

**Jaeger** (distributed tracing):
- A "trace" = a run_id (our EdgeRun) with child "spans" (our iterations)
- Trace ID lookup is O(1) via hash index
- Span data is stored per-trace, not in a flat event log
- Lesson: index by run_id at ingest; serve trace detail from per-run store

---

## Decision

Replace the current full-load projection model with an **event index** that enables
O(log n) queries instead of O(n) full scans on every request.

### Architecture

```
events.jsonl (append-only source of truth)
    │
    ▼
EventIndex (built once at startup, updated incrementally on file change)
    ├── by_time: SortedList[Event]         — range queries (scrubber)
    ├── by_run: dict[run_id, EdgeRun]      — trace lookup (O(1))
    ├── by_feature: dict[feature, list[EdgeRun]]  — feature lineage (O(1))
    ├── by_edge: dict[edge, list[EdgeRun]] — edge filter (O(1))
    └── by_day: dict[date, list[EdgeRun]]  — timeline pagination (O(1))

HTTP Request
    │  uses
    ▼
Query API (thin layer over EventIndex)
    ├── timeline(feature?, edge?, status?, since?, until?) → list[EdgeRun]
    ├── feature_lineage(feature_id) → list[EdgeRun]
    ├── run_detail(run_id) → EdgeRun
    └── state_at(t: datetime) → ProjectState  (replay)
```

### EventIndex Build

Built once at startup from `events.jsonl`:
1. Parse all events (one pass, O(n))
2. Group into EdgeRuns (one pass, O(n)) — same algorithm as `build_edge_runs()`
3. Build all secondary indices (one pass over EdgeRuns, O(m) where m << n)
4. Store index in memory

Incremental update on file change (watchdog):
1. Read new lines appended since last read position (file offset tracking)
2. Parse new events, route to open EdgeRuns or create new ones
3. Update all secondary indices for affected runs only
4. No full rebuild needed

### Memory Model

```
RAM usage ≈ sizeof(EventIndex)
         = n_events × ~200 bytes (compressed Event) + m_runs × ~500 bytes (EdgeRun metadata)
         ≈ 100k events → ~20 MB     (fine)
         ≈ 1M events  → ~200 MB     (borderline — add hot/cold split at this scale)
```

For the current dogfood scale (1500 events, 133 runs), this is trivial. The index is the
correct abstraction even at small scale because it enables clean API boundaries.

### Hot/Cold Split (future — when >100k events)

At large scale, apply the Prometheus pattern:
- **Hot segment**: events from the last 24h — always in memory
- **Cold segments**: events older than 24h — memory-mapped blocks (one file per day)
- Range queries on cold data via mmap, lazy-loaded page fault
- Only hot segment kept warm; cold data loaded on demand

This is not needed now. The index abstraction makes it a drop-in replacement later.

---

## Implementation Plan

### Phase 1 (immediate — dogfood scale)
- Create `genesis_monitor/index.py` — EventIndex class with build_from_events()
- Migrate `registry.py` to store EventIndex per project alongside events list
- Migrate routes to use EventIndex.timeline() / .feature_lineage() / .run_detail()
- Remove `build_edge_runs()` call from request path (move to index build time)

### Phase 2 (incremental updates)
- Track file offset in EventIndex
- On watchdog file change: read new lines, partial update of index
- Emit SSE "timeline_updated" event for live timeline refresh

### Phase 3 (state reconstruction / replay)
- Add EventIndex.state_at(t) — returns ProjectState derived from events[:t]
- Powers the time-travel scrubber (REQ-F-EVOL-001)
- O(log n) via binary search on by_time

---

## Consequences

**Positive**:
- Request latency: O(1) to O(log n) instead of O(n) — timeline loads instantly even at 100k events
- Incremental SSE updates: new events append to index without full rebuild
- Clean API: routes express queries, not projection logic
- Testable: EventIndex is a pure data structure, easily unit-tested

**Negative**:
- Additional startup time for index build (one-time, O(n) — acceptable)
- Index memory footprint (scales linearly — acceptable at target scale)
- More complex code than the current simple list comprehensions

**Neutral**:
- No external dependencies: the index is a plain Python data structure
- The event log remains the source of truth — the index is always rebuildable

---

## Relation to Jaeger/Prometheus/Loki

| Concept | Jaeger | Our System |
|---------|--------|------------|
| Trace | End-to-end request span tree | EdgeRun (edge_started → N iterations → edge_converged) |
| Span | Individual operation | IterationSummary |
| Trace ID | Unique UUID | run_id (OL runId or synthesised) |
| Service | Microservice | Feature (REQ-F-*) |
| Operation | Handler name | Edge name (code↔unit_tests) |

The OL event stream IS a distributed trace. The EdgeRun grouping IS trace reconstruction.
The EventIndex IS the trace store. We're building a domain-specific Jaeger for SDLC operations.

The key insight from Prometheus is that **time-series data must be indexed, not scanned**.
Every Prometheus query is a range scan over pre-computed chunks, not a grep over raw logs.
We apply the same principle: build the EdgeRun index once, query it many times.
