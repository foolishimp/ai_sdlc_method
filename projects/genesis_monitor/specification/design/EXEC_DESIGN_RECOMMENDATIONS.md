# Design Recommendations: Executor Attribution & Observability Debt
<!-- Traces-To: REQ-F-EXEC-001, REQ-F-EXEC-002, REQ-F-EXEC-003 -->
<!-- Edge: feature_decomposition→design_recommendations -->
<!-- Iteration: 1 | Status: candidate -->
<!-- Source asset: specification/features/EXEC_FEATURE_DECOMPOSITION.md -->
<!-- Stack: Python 3.11 + FastAPI + HTMX + D3.js v7 (CDN) -->

---

## Design Scope

MVP scope per feature decomposition:

- **EXEC-001** — Executor Attribution Parsing (foundational; all others depend on this)
- **EXEC-002** — Topology Trail Executor Arc Styling
- **EXEC-003** — Executor Badge in Edge Convergence Table

Deferred:
- **EXEC-004** — Observability Debt Summary (no trend data yet; deferred per decomp rationale)

---

## ADR-EXEC-001: Executor Fields on Event Base Class

**Status**: Accepted

**Context**:
Events in `.ai-workspace/events/events.jsonl` are emitted by two paths:
1. **Engine path** (OL-format) — emitted by `imp_claude/code/genesis/ol_event.py`. Identified by presence of `eventType` key.
2. **Claude path** (flat-format) — emitted by methodology commands (`gen-iterate`, `gen-checkpoint`, etc.). Identified by presence of `event_type` key (snake_case) without `eventType`.

Neither format currently includes `executor` or `emission` fields. Attribution must be inferred.

**Decision**:
Add `executor: str` and `emission: str` as optional fields to the `Event` base class in `models/events.py`. Default both to empty string; inference sets them at parse time.

**Rationale**:
- Placing fields on the base class (not subtypes) means every projection, template, and view can access them uniformly — no isinstance guards needed downstream.
- Keeping them as `str` (not an enum) allows the model to absorb future attribution values without a schema change.

**Inference Rules (deterministic)**:

| Condition | `executor` | `emission` |
|-----------|-----------|-----------|
| Raw event has `eventType` (OL-format) | `"engine"` | `"live"` (unless explicit `retroactive`) |
| Raw event has `event_type`, no `eventType` (flat-format) | `"claude"` | `"live"` (unless explicit `retroactive`) |
| Raw event has explicit `executor` field | use field value | — |
| Raw event has explicit `emission` field | — | use field value |
| Neither format detected | `"unknown"` | `"live"` |

Inference runs at the end of `_parse_one()` and `_parse_flat()` in `parsers/events.py` — after all other field mapping — so explicit values in the raw data always win.

**Implementation site**: `parsers/events.py` — `_parse_one()` and `_parse_flat()`.

---

## ADR-EXEC-002: Executor Attribution on EdgeRun

**Status**: Accepted

**Context**:
`EdgeRun` in `projections/edge_runs.py` is the per-edge traversal summary consumed by all views. The convergence table and D3 topology trail both read from `EdgeRun`. Attribution at the run level (not per-iteration) is the correct granularity for UI display — the executor that produced convergence is what matters.

**Decision**:
Add `executor: str = ""` and `emission: str = ""` fields to the `EdgeRun` dataclass. Populate them in `_close_run()` from the closing event's `executor`/`emission` fields.

**Fallback**: if the closing event has no executor (e.g. synthesised run), walk `raw_events` in reverse and use the first event with a non-empty executor.

**Rationale**:
- A single attribution per run matches the UX: one arc style, one badge — not a per-iteration display.
- Deriving it from the closing event is semantically correct: the executor that produced convergence is the attribution.
- Fallback covers synthesised runs (iteration without edge_started) which are common for retroactively logged events.

**Implementation site**: `projections/edge_runs.py` — `EdgeRun` dataclass + `_close_run()`.

---

## ADR-EXEC-003: Arc Styling Strategy for Topology Trail

**Status**: Accepted

**Context**:
The Topology Trail uses D3.js v7 (CDN, no build step) to render edge arcs, established in ADR-007. Arcs are SVG `<path>` elements with a stroke. Three visual styles are needed for executor attribution.

**Decision**:
Use CSS `stroke-dasharray` to distinguish executor types. No JS changes beyond passing the style class. Existing arc rendering in `projections/graph.py` (`_build_graph_data()`) will add a `style` field to each arc object. The D3 render function in `timeline.html` applies it as a CSS class.

**Style mapping**:

| `executor` value | Arc style | CSS class | `stroke-dasharray` |
|-----------------|-----------|-----------|-------------------|
| `"engine"` | Solid | `arc-engine` | `none` |
| `"claude"` | Dashed | `arc-claude` | `8 4` |
| `"retroactive"` | Dotted amber | `arc-retroactive` | `2 4` |
| `"unknown"` (fallback) | Solid (conservative) | `arc-engine` | `none` |

**Arc legend**: A static SVG legend block added below the D3 canvas. Three rows: solid/dashed/dotted with label.

**Rationale**:
- `stroke-dasharray` works on SVG paths with no JS library changes — zero additional dependencies.
- Defaulting `unknown` to `arc-engine` (solid) is conservative: it avoids false negative signals (no spurious debt indicators for events from old runs before this feature shipped).
- A static legend (not JS-rendered) is consistent with the project constraint: "No JavaScript build tooling."

**Implementation sites**:
- `projections/graph.py` — `_build_graph_data()` adds `style: str` to arc dicts
- `server/` templates — CSS classes + legend block

---

## ADR-EXEC-004: Executor Badge Component

**Status**: Accepted

**Context**:
The Edge Convergence table (served by `server/routes.py`) displays one row per converged edge run. A new "Executor" column will show a small badge indicating attribution.

**Decision**:
Add a new `<td class="executor-badge">` column to the convergence table template. Badge is a `<span>` with a CSS class derived from the `executor` field of the `EdgeRun`.

**Badge mapping**:

| `executor` | Badge label | CSS class | Colour |
|-----------|-------------|-----------|--------|
| `"engine"` | `engine` | `badge-engine` | Green |
| `"claude"` | `claude` | `badge-claude` | Blue |
| `"retroactive"` | `retroactive` | `badge-retroactive` | Amber |
| `"unknown"` / empty | `unknown` | `badge-unknown` | Grey |

**No false confidence**: rows with empty attribution show `unknown` rather than a blank or defaulting to engine. This makes the observability gap visible at a glance.

**Rationale**:
- Badge styling mirrors the arc styling visual language from ADR-EXEC-003 — same colour associations, consistent lexicon.
- HTMX partial refresh: the convergence table is served as an HTMX fragment; no additional route needed for the badge column — it is a template-only change.

**Implementation sites**:
- Template rendering the edge convergence table (server-side Jinja2)
- `server/routes.py` — passes `edge_run.executor` into template context (already done once `EdgeRun.executor` is populated)

---

## Build Order

1. **EXEC-001** (ADR-EXEC-001 + ADR-EXEC-002):
   - Add `executor`, `emission` to `Event` in `models/events.py`
   - Add inference logic in `parsers/events.py` (`_parse_one`, `_parse_flat`)
   - Add `executor`, `emission` to `EdgeRun` in `projections/edge_runs.py`
   - Populate in `_close_run()` + fallback walk

2. **EXEC-002 + EXEC-003** (parallel after EXEC-001):
   - EXEC-002: Arc style field in `_build_graph_data()` + CSS + legend in template
   - EXEC-003: Executor badge column in convergence table template + CSS

3. **Tests** (each sub-feature has unit tests before integration):
   - EXEC-001: `test_executor_attribution.py` — inference rules, edge cases
   - EXEC-002: `test_graph_arc_style.py` — arc data generation
   - EXEC-003: Extend existing convergence table tests

---

## Source Findings

| Finding | Classification | Disposition |
|---------|---------------|-------------|
| `eventType` presence is reliable across all OL events tested | SOURCE_CONFIRMED | Inference on this key is deterministic |
| Retroactive events are distinguished by an explicit `emission: retroactive` field | SOURCE_AMBIGUITY | Resolved: inference defaults to `live`; `retroactive` only when explicit |
| Old events (before this feature) have no attribution fields | SOURCE_GAP | Resolved: `unknown` badge + solid arc (conservative default) |
| The D3 arc renderer expects `style` per-arc; current implementation has no style field | SOURCE_GAP | Resolved: add `style` field to arc dict in `_build_graph_data()` |

---

## Evaluator Checklist (edge: design_recommendations)

| Check | Type | Required |
|-------|------|----------|
| All ADR decisions have a rationale section | agent | yes |
| Technology bindings are explicit (no TBD) | agent | yes |
| Inference rules are deterministic (no LLM-dependent logic) | agent | yes |
| Build order respects dependency DAG from feature decomposition | deterministic | yes |
| No new external dependencies introduced | agent | yes |
| CSS-only arc styling confirmed (no JS library changes) | agent | yes |
| Badge visual language consistent with arc visual language | agent | yes |
| Source findings documented | agent | yes |

---

## Process Gaps

None identified. Inference rules are deterministic. Stack constraints (no JS build) are satisfied by CSS `stroke-dasharray`. Badge column is a pure template change.
