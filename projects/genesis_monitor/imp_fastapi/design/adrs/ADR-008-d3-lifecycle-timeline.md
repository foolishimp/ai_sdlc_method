# ADR-008: D3.js Time Series Lifecycle View — Second Visualization Projection

**Status**: Accepted
**Date**: 2026-03-08
**Implements**: REQ-F-TSER-001, REQ-F-TSER-002, REQ-F-TSER-003, REQ-F-TSER-004
**Intent**: INT-GMON-011

---

## Context

The topology trail graph (ADR-007, INT-GMON-010) answers "what paths does the project take through
the methodology graph?" It is a structural projection — nodes are asset types, arcs are EdgeRuns.

INT-GMON-011 requires a second, orthogonal projection: a **time series view** where the X-axis is
wall-clock time and each feature occupies a horizontal swimlane. EdgeRuns appear as bars whose
width is proportional to their real-world duration. This answers:

- "When did each phase happen?"
- "How long did each edge traversal take?"
- "Where are the gaps — periods of no activity?"
- "Were features built in parallel or sequentially?"
- "Which edges required many iterations (thick effort bars)?"

These are **operational and debugging questions** that the topology view cannot answer. The two
projections are complementary, not redundant.

---

## Decision

Implement the lifecycle view as a **second D3.js visualization** on the same timeline page,
tab-switched with the topology trail graph.

**Technology**: D3.js v7 (already loaded for the trail graph — zero additional CDN cost).

**Data source**: The existing `GET /project/{id}/timeline/graph-data` JSON endpoint, extended
with `ended_at` (ISO string or null) and `duration_seconds` (float or null) per run.

**Architecture**: The page fetches graph-data **once** on load. The trail graph renders immediately.
The lifecycle view is **lazy-initialized** on first tab activation — no second network request,
no redundant computation.

---

## Design

### Layout

```
[Topology Trail] [Lifecycle]   ← tab switcher (above visualization area)

┌────────────────────────────────────────────────────────────────────┐
│ [Fit] [1h] [1d] [1w]                                               │ ← zoom controls
│                                                                     │
│ REQ-F-GMON-001 ├════intent→req═╡  ╞════req→design════╡             │ ← swimlane
│ REQ-F-GMON-004 │                         ╞══design→code══╡         │
│ REQ-F-GVIZ-001 │                              ╞═code↔tests═╡       │
│                │                                                    │
│ Feb 21       Mar 1         Mar 7         Mar 8                      │ ← time axis
└────────────────────────────────────────────────────────────────────┘
```

### Swimlane Ordering

Features are sorted top-to-bottom by their earliest `started_at` timestamp — features that
started earliest appear at the top. This makes the "build order" readable: newer features
appear below older ones, reflecting the project's growth.

### Bar Encoding

| Visual | Encoding | Notes |
|--------|---------|-------|
| Left edge | `started_at` | Wall-clock position |
| Width | `ended_at - started_at` (or now - started_at) | Duration proportional |
| Fill | Feature colour (Tableau-10 palette, stable) | Same as trail graph |
| Opacity | 0.85 (converged), 0.65 (in_progress), 0.85 (failed) | Status |
| Border | Red/warning stroke for failed/aborted | Status severity |
| Label | Edge name inside bar (if ≥ 40px wide) | Truncated if needed |
| Badge | Iteration count top-right (if > 1 and ≥ 20px wide) | Effort signal |
| Animation | Pulse for in_progress | Live activity |

### Gap Visibility

Gaps are **zero-cost**: empty horizontal space on the time axis IS the gap. No special rendering
needed. The time scale makes gaps visually obvious — a feature lane with two widely-separated
bars shows clearly that nothing happened in between.

### Zoom

`d3.zoom()` constrains horizontal zoom only (Y-axis does not scroll). The original `d3.scaleTime()`
is preserved; zoom applies `event.transform.rescaleX(xOrig)` to get the current view scale. This
means bars and axis update together with no coordinate inconsistency.

Preset buttons use `d3.zoom.transform()` to set specific scale/translate values — they "look back"
from the most recent event, so "1h" shows the last hour of activity.

### Data Lifecycle

```
page load
  → fetch /graph-data (one request)
  → graphData stored as module variable
  → trail graph rendered immediately

user clicks "Lifecycle" tab
  → initLifecycle(graphData) called once
  → D3 renders SVG from in-memory data
  → subsequent tab switches show/hide (no re-render)
```

---

## Consequences

**Positive**:
- Zero additional network requests — shares graph-data fetch with trail graph
- Zero additional CDN load — D3.js v7 already loaded
- Lazy initialization — no cost if user never visits the Lifecycle tab
- Time-scale zoom enables viewing from "whole project" to "single iteration" in seconds
- Gap visibility is free — empty space IS the signal

**Negative**:
- An additional ~150 lines of D3 code in timeline.html (no external module)
- `ended_at` and `duration_seconds` added to graph-data response (minor payload increase)

**Neutral**:
- The two visualizations share the same data model, palette, and filter interactions
- Clicking a feature label in lifecycle calls `selectGraphFeature()` from the trail graph — the
  two views coordinate without needing an event bus
