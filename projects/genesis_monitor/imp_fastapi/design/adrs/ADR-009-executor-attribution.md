# ADR-009: Executor Attribution — Inference, Arc Styling, and Convergence Badge

**Status**: Accepted
**Date**: 2026-03-09
**Implements**: REQ-F-EXEC-001, REQ-F-EXEC-002, REQ-F-EXEC-003
**Source**: specification/design/EXEC_DESIGN_RECOMMENDATIONS.md

---

## Context

Events in `.ai-workspace/events/events.jsonl` are produced by two paths: the Python
engine (OL-format, `eventType` key) and methodology commands (flat-format, `event_type`
key). Neither format includes explicit `executor` or `emission` attribution fields in
existing runs.

Genesis Monitor needs to surface which execution path produced each convergence:
- **engine** — F_D deterministic evaluation (Python engine, `ol_event.py`)
- **claude** — F_P live emission (gen-iterate commands)
- **retroactive** — observability debt filled post-hoc

---

## Decision

### 1. Event Model (models/events.py)

Add two optional string fields to the `Event` base dataclass:

```python
executor: str = ""   # "engine" | "claude" | "retroactive" | "unknown"
emission: str = ""   # "live" | "retroactive"
```

Placed on base class — all projections and templates access uniformly without isinstance guards.

### 2. Inference (parsers/events.py)

Apply at the end of `_parse_one()` and `_parse_flat()`, after all other field mapping,
so explicit values in raw data always win:

| Condition | executor | emission |
|-----------|----------|----------|
| `eventType` key present (OL-format) | `"engine"` | `"live"` |
| `event_type` key only (flat-format) | `"claude"` | `"live"` |
| explicit `executor` field in raw data | raw value | — |
| explicit `emission: retroactive` in raw data | — | `"retroactive"` |
| no format detected | `"unknown"` | `"live"` |

### 3. EdgeRun attribution (projections/edge_runs.py)

Add `executor: str = ""` and `emission: str = ""` to `EdgeRun`. Populate in
`_close_run()` from the closing event's fields. Fallback: walk `raw_events` in
reverse for first event with non-empty executor.

### 4. Arc Styling (projections/graph.py + templates)

Add `style: str` field to each arc dict in `_build_graph_data()`:

| executor | style | stroke-dasharray |
|----------|-------|-----------------|
| engine / unknown | `"arc-engine"` | none (solid) |
| claude | `"arc-claude"` | 8 4 (dashed) |
| retroactive | `"arc-retroactive"` | 2 4 (dotted amber) |

D3 arc renderer applies style as a CSS class. Static SVG legend added below canvas.

### 5. Convergence Badge (server templates)

Add "Executor" column to edge convergence table:

| executor | badge label | CSS class | colour |
|----------|-------------|-----------|--------|
| engine | `engine` | `badge-engine` | green |
| claude | `claude` | `badge-claude` | blue |
| retroactive | `retroactive` | `badge-retroactive` | amber |
| unknown / empty | `unknown` | `badge-unknown` | grey |

Badge shows `unknown` (not blank) for rows without attribution — makes debt visible.

---

## Consequences

- No new external dependencies. CSS `stroke-dasharray` works on existing SVG paths.
- Conservative default: `unknown` → solid arc + grey badge avoids false debt signals for
  pre-feature events.
- When explicit `executor` field is added to future events, inference is bypassed
  automatically (field-value takes precedence).
- EXEC-004 (Observability Debt Summary) is deferred; this ADR does not address it.
