# ADR-007: D3.js Event Trail Graph — Visualization Technology Binding

**Status**: Accepted
**Date**: 2026-03-08
**Implements**: REQ-F-GVIZ-001, REQ-F-GVIZ-002, REQ-F-GVIZ-003, REQ-F-GVIZ-004, REQ-F-GVIZ-005
**Intent**: INT-GMON-010

---

## Context

REQ-F-GVIZ-001..005 specify an "Event Trail Graph" — a visualization of the methodology graph where
nodes are asset types and arcs are EdgeRuns. The requirements demand:

- Interactive arc selection with table synchronisation (REQ-F-GVIZ-003)
- Per-arc encoding of iteration effort, status, and recency (REQ-F-GVIZ-002)
- Per-node encoding of aggregate health (REQ-F-GVIZ-004)
- Feature legend with colour identity and toggle controls (REQ-F-GVIZ-005)
- Animation for in-progress runs (REQ-F-GVIZ-002 AC-7)

The core constraint from the system's technology profile (REQ-NFR-001, ADR-003):
- **No JS framework** — no React, Vue, or build step
- **No npm/webpack** — libraries loaded from CDN only
- **No new server-side dependencies** — Python/FastAPI stack is fixed

A static Mermaid diagram (already used elsewhere in the monitor) cannot satisfy the
interactivity or dynamic data binding requirements.

---

## Options Considered

### Option A: Mermaid.js (already in use)
Mermaid renders DAG diagrams from text. Cannot encode per-arc stroke width, opacity, feature
colour, animation, or interactive selection. Rejected — wrong tool for the problem.

### Option B: Pure SVG from Jinja2 (server-rendered)
Server computes all arc positions and emits raw `<svg>` + `<path>` elements. Interactive
events handled via HTMX + URL params (page reload on click).

- Pro: No client-side JS library. Fully server-controlled.
- Con: No hover tooltips, no smooth arc highlighting, no opacity transitions, no animation.
  Violates REQ-F-GVIZ-002 (animation) and REQ-F-GVIZ-003 (client-side de-emphasis without reload).

Rejected — cannot meet interactivity requirements without client-side execution.

### Option C: D3.js v7 from CDN (selected)
D3.js is the canonical SVG data visualization library. It binds data to DOM elements, handles
geometric calculations (Bezier paths, force layout), and provides event APIs.

- CDN: `https://d3js.org/d3.v7.min.js` — no npm, no build step.
- Pro: Precise control over arc geometry, colour, stroke, opacity, and animation.
  Native event handling for click/hover. Stable API (D3 v7 LTS).
- Pro: JSON data endpoint is a natural separation — server computes graph data, D3 renders it.
- Con: ~250 KB CDN load (one-time, cached). Requires inline JS in the template.
- Neutral: D3 is not a framework — it is a vocabulary for SVG manipulation. No component model,
  no state management, no build target. Satisfies the "no framework" constraint.

Accepted.

---

## Decision

**D3.js v7** (CDN, no build step) renders the Event Trail Graph client-side.

A new JSON endpoint `/project/{id}/timeline/graph-data` provides the graph data:
server-computed node positions (x_order), run attributes, and feature colours.
D3.js fetches this endpoint on page load and renders the SVG in-browser.

---

## Architecture

```
Server                              Browser
──────                              ───────

GET /project/{id}/timeline          timeline.html loads
  → timeline.html                     D3.js from CDN
     (includes #trail-graph div)      fetches graph-data JSON
                                      renders SVG arcs + nodes
GET /project/{id}/timeline/graph-data
  → JSON: {nodes, runs, features}   D3 handles:
       (from EventIndex)               - arc click → filter bar update
                                       - node click → node filter
                                       - row de-emphasis (client-side CSS)
                                       - hover tooltips (title element)
                                       - arc animation (CSS keyframes)
```

### JSON Schema

```json
{
  "project_id": "string",
  "nodes": [
    {
      "id": "intent",
      "label": "Intent",
      "x_order": 0,
      "total_runs": 3,
      "converged_count": 3,
      "in_progress_count": 0,
      "failed_count": 0
    }
  ],
  "runs": [
    {
      "run_id": "string",
      "feature": "REQ-F-GMON-001",
      "edge": "intent→requirements",
      "source": "intent",
      "target": "requirements",
      "status": "converged",
      "iteration_count": 1,
      "final_delta": 0,
      "started_at": "2026-02-21T08:00:00+00:00",
      "colour_index": 0
    }
  ],
  "features": [
    {
      "id": "REQ-F-GMON-001",
      "colour_index": 0,
      "run_count": 4,
      "status": "converged"
    }
  ]
}
```

### Node Layout

Canonical SDLC order (REQ-F-GVIZ-001 AC-2):

```
intent → requirements → feature_decomposition → design → module_decomposition →
basis_projections → code → unit_tests → uat_tests → cicd → telemetry
```

Nodes are spaced evenly on the x-axis (fixed positions). Unknown asset types are
appended at the right. Y is fixed at SVG midline. This gives the "left=inception,
right=production" spatial metaphor without any force simulation.

### Arc Geometry (REQ-F-GVIZ-002)

Each arc is a quadratic Bezier path `M src Q ctrl tgt`:
- Control point x: midpoint of source and target x
- Control point y: midY + bundle_offset, where bundle_offset = (arc_index - n/2) × 30 - 40

This produces a fan of arcs above the node line. Multiple runs on the same edge are
visually separable without overlap.

Arc encoding:
| Attribute | Encoding | Formula |
|-----------|---------|---------|
| `stroke-width` | Iteration effort | `log1p(n_iterations) × 2 + 1` (logarithmic) |
| `stroke` | Feature colour | `PALETTE[colour_index % 10]` (Tableau-10) |
| `stroke-opacity` | Recency | `0.3 + 0.7 × (t - t_min) / (t_max - t_min)` |
| `stroke-dasharray` | Status | solid (converged), `8 4` (in_progress), `3 3` (failed/aborted) |
| `animation` | In-progress | `stroke-dashoffset` travelling dash (CSS keyframe) |

### Node Encoding (REQ-F-GVIZ-004)

| Attribute | Encoding |
|-----------|---------|
| `r` (radius) | `clamp(8 + log1p(total_runs) × 4, 12, 24)` |
| `fill` | red (any failed) > amber (any in_progress) > green (all converged) > neutral |
| `animation` | Pulse if any in_progress runs |

### Interaction Model (REQ-F-GVIZ-003)

Client-side only — no page reload required:

1. Arc click → calls `selectArc(feature, edge)`:
   - Updates filter bar `input[name=feature]` and `input[name=edge]` values
   - Adds `.dimmed` CSS class to non-matching arcs (opacity: 0.15)
   - Sets `style.opacity = 0.35` on non-matching `.run-row` elements
   - Does NOT reload the page (user must click Filter to apply)

2. Node click → calls `selectNode(nodeId)`:
   - Sets edge filter input to nodeId substring (matches any edge touching that node)

3. SVG background click → clears selection (removes `.dimmed`, resets row opacity)

4. Filter form submit → standard GET request; page reloads with URL params
   → D3 reads URL params on load and pre-highlights matching arcs

This satisfies AC-1 (de-emphasis not hide), AC-2 (node click), AC-3 (clear),
AC-4 (tooltip via `<title>`), AC-5 (filter bar reflects selection), AC-7 (URL params → pre-highlight).

AC-6 (URL reflects selection on arc click) is satisfied at Filter form submit — clicking an arc
populates the filter bar; submitting the form updates the URL. True URL-on-click would require
`history.pushState` (deferred to a future iteration as it requires additional complexity).

### Legend (REQ-F-GVIZ-005)

HTML div `#trail-legend` rendered by D3 after graph data loads:
- One row per feature: colour swatch, feature ID, status icon, run count
- Click row → calls `selectArc(feature_id, null)`
- Features sorted: in_progress first, then failed, then converged (AC-4)
- "Select all / Deselect all" link clears active selection

---

## Implementation Plan

| Component | File | Change |
|-----------|------|--------|
| JSON data endpoint | `server/routes.py` | Add `GET /project/{id}/timeline/graph-data` + `_build_graph_data()` helper |
| Graph section | `templates/timeline.html` | Add `#trail-graph` div + D3.js CDN script before filter bar |
| JSON response model | `server/routes.py` | `_build_graph_data()` — pure function, no model imports needed |
| Tests | `tests/test_event_index.py` or `test_graph_viz.py` | Graph data correctness, edge parsing, node ordering |

No new Python modules needed. The `_build_graph_data()` helper is a pure function that
operates on `list[EdgeRun]` — it belongs in `routes.py` as a file-local function since
it is view-layer aggregation.

---

## Consequences

**Positive**:
- Rich interactive visualization satisfying all 5 REQ-F-GVIZ requirements
- D3.js handles all geometry — server only provides data, not pixel coordinates
- No build step — single CDN script tag
- The JSON endpoint is reusable for future visualizations (e.g. dashboard widgets)

**Negative**:
- ~250 KB CDN dependency (D3 v7 minified, loaded once and cached)
- Inline JS in timeline.html is harder to test than a separate module
- True bookmarkable URL-on-arc-click deferred (filter form submit satisfies practical need)

**Neutral**:
- D3.js is well-established, stable, and widely understood — low risk
- The JSON endpoint is plain FastAPI — testable with `TestClient` like all other routes

---

## Alternatives Not Explored

- **Observable Plot** — newer D3 abstraction, ESM-only, requires build step
- **Vis.js network** — force-directed, not suitable for the fixed horizontal SDLC layout
- **Cytoscape.js** — feature-rich graph library; overkill for this use case, heavier CDN load
