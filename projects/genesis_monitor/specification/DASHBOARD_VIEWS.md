# Genesis Monitor — Dashboard View Specification

**Version**: 2.0.0
**Date**: 2026-03-08
**Status**: Active — drives imp_fastapi design + code iteration
**Traces To**: INT-GMON-001, INT-GMON-004, INT-GMON-009, INT-GMON-010, INT-GMON-011

---

## Design Principles

1. **No duplicate views** — each piece of information has exactly one primary location.
2. **Three questions, three answers** — every panel answers exactly one of: *what happened*, *what's going on*, *why*.
3. **Time picker = data filter; D3 zoom = viewport** — these are different concerns and must not compete.
4. **Events are first-class** — escalations, reviews, findings are as important as convergence metrics.
5. **Causation chains are visible** — `finding → intent → spec_mod → spawn` must read as a narrative, not scattered rows.

---

## Data Model Available

Understanding what we have before specifying views:

### EdgeRun (the unit of work — like a distributed trace span)
```
run_id           unique per traversal
feature          REQ-F-* identifier
edge             e.g. "code↔unit_tests"
started_at       wall-clock start
ended_at         wall-clock end (None if in_progress)
status           in_progress | converged | failed | aborted
convergence_type standard | question_answered | time_box_expired
iterations[]     each iterate() cycle:
  iteration        count
  timestamp        when this cycle ran
  delta            failing check count (0 = converged)
  evaluators_passed / failed / skipped / total
  evaluator_details[]  check_name, check_type, result, expected, observed
artifacts[]      file paths written during this run
```

### Decision Events (the "why" — currently invisible)
```
convergence_escalated   edge, reason, escalated_to
review_completed        edge, feature, reviewer, outcome (approved|changes_requested|deferred)
encoding_escalated      edge, feature, previous_valence, new_valence, trigger
intent_raised           trigger, signal_source, prior_intents[]
spec_modified           previous_hash, new_hash, delta (summary), trigger_intent
finding_raised          finding_type (backward|forward|inward), description, edge, feature
feature_spawned         parent_vector, child_vector, reason (gap|risk|feasibility|scope)
feature_folded_back     parent_vector, child_vector, outputs[]
claim_rejected          agent_id, edge, reason
iteration_abandoned     edge, feature, iteration, reason
```

### Sensory Events (the environment — currently invisible)
```
interoceptive_signal    signal_type, measurement, threshold, valence
exteroceptive_signal    source, signal_type, payload, valence
affect_triage           signal_ref, triage_result (reflex|escalate|ignore), rationale
```

### Feature Vector (current state — derived from events)
```
feature_id      REQ-F-*
title           human label
status          converged | in_progress | pending
trajectory      edge → {status, iteration, started_at, converged_at}
profile         standard | hotfix | spike
parent_id       if spawned
children[]      child REQ-F-* IDs
```

---

## Global Time Controls

**The existing dual-slider scrubber is replaced by a Grafana-style time picker.**

### Time Picker (data filter — controls ALL panels)

```
[Last 1h]  [6h]  [1d]  [1w]  [All]  [  2026-03-01 → 2026-03-08  ▾ ]  [↻ Live]
```

Changing the time range re-fetches all HTMX panels with `?t_from=&t_to=` params.
The backend filters the EventIndex: `index.timeline(since=t_from, until=t_to)`.

- **Live mode** (default): no `t_from`/`t_to`; SSE pushes updates in real time.
- **Historical mode**: time range set; SSE disconnected; panels reflect the frozen slice.
- Presets: Last 1h / 6h / 1d / 1w / All time.
- Custom: date-time picker inputs (no calendar library needed — HTML `<input type="datetime-local">`).

### Local D3 Zoom (viewport — affects only D3 visualizations)

The D3 Lifecycle and Trail views have their own horizontal zoom. This zooms the viewport
within the loaded data window — it does NOT re-fetch data. It is `d3.zoom()` territory.

**The two must not interfere:**
- Time picker → server round-trip → new data loaded
- D3 zoom → client-side rescale → same data, different viewport

**Connection between them:** When the user zooms deep in D3, an optional "Set as time range" button
appears, which reads the current D3 x-domain and pre-fills the time picker inputs.
This bridges local zoom → global filter without conflating them.

---

## Page Inventory

| Page | URL | Answers |
|------|-----|---------|
| **Project Index** | `/` | At a glance: which projects exist and their health |
| **Project Dashboard** | `/project/{id}` | What's going on + Why |
| **Edge Timeline** | `/project/{id}/timeline` | What happened (traces + topology) |
| **Feature Lineage** | `/project/{id}/feature/{fid}` | One feature's full artifact trail |
| **Artifact Viewer** | `/project/{id}/artifact?path=…` | Raw file contents |

---

## Page: Project Index (`/`)

One card per project. Cards sorted by last-event timestamp (most active first).

```
┌──────────────────────────────────────────────────────┐
│  Genesis Monitor (imp_fastapi)                        │
│  /Users/jim/src/apps/ai_sdlc_method/projects/…       │
│                                                       │
│  ✓ 9 converged  ⟳ 0 in-progress  · 2 pending         │
│  100 events · Last activity: 12:49 today              │
│                                                       │
│  [Open Dashboard]   [Edge Timeline →]                 │
└──────────────────────────────────────────────────────┘
```

No tree hierarchy. No tables. Cards only.

---

## Page: Project Dashboard (`/project/{id}`)

Answers: **What's going on?** and **Why?**

The time picker sits at the top of this page (below the project header).

### Section 1 — Project Header

```
Genesis Monitor (imp_fastapi)   [Bootloader ✓]
/Users/jim/src/apps/ai_sdlc_method/projects/genesis_monitor

[Edge Traversal Timeline →]

Time: [Last 1h] [6h] [1d] [1w] [All] [Custom…]  ↻ Live

Design tenant: [All tenants (100)] [imp_fastapi (72)] [imp_gemini (28)]
```

### Section 2 — Feature Matrix (What's going on — convergence state)

Rows = features. Columns = edges that appear in THIS project's topology only.
Not all possible edges — only those recorded in the event log.

```
Feature                                  intent  req  design  code  tests  uat
REQ-F-GMON-001 Core Monitoring & Disc.    ✓       ✓    ✓       ✓     ✓      —
REQ-F-GMON-002 Real-time Dashboard        ✓       ✓    ✓       ✓ 2   ✓      —
REQ-F-GMON-005 CQRS Hierarchy             ✓       ·    ·       ·     ·      —
REQ-F-GVIZ-001 Event Trail Graph          —       ✓    ✓       ✓     ✓      —
```

**Status symbols:**
| Symbol | Meaning |
|--------|---------|
| `✓` | converged (iteration 1 implied; show `✓ N` if N > 1) |
| `⟳ N` | in_progress (N = current iteration) |
| `·` | pending (not started) |
| `✗` | failed or aborted |
| `!` | escalated (convergence_escalated emitted for this edge) — red badge |
| `👁` | review_pending (review_completed not yet received) |
| `—` | not applicable (edge not in feature's profile) |

The `!` escalation badge is new and critical — visible at a glance.

**Interactions:**
- Click feature row label → `/project/{id}/feature/{fid}` (Feature Lineage)
- Click edge cell with runs → `/project/{id}/timeline?feature={fid}&edge={edge}`
- Click edge column header → `/project/{id}/timeline?edge={edge}`

**Replaces:** Feature Vectors card grid + Gantt/Timeline matrix (both removed).

### Section 3 — Edge Summary (What's going on — per-edge health)

Single unified table. Replaces Edge Convergence AND Edge Status (both removed).

| Edge | Status | Runs | Iterations | Features | Duration | Notes |
|------|--------|------|-----------|---------|---------|-------|
| intent→req | converged | 4 | 12 | 4 | 347h | — |
| req→design | converged | 5 | 23 | 5 | 352h | standard |
| code↔tests | in_progress | 6 | 42 | 6 | 351h | co-evolution |
| code↔tests | ⚠ escalated | — | — | 1 | — | review pending |

**Columns:**
- **Runs** — count of distinct EdgeRun objects (traversals)
- **Iterations** — total `iterate()` cycles across all runs on this edge
- **Features** — count of features that have run on this edge
- **Duration** — total wall-clock (all runs combined)
- **Notes** — convergence_type (standard/time_box/escalated) or escalation warning

The **delta_curve** `[0,0,2,1,0]` is removed from this overview — it belongs in edge drill-down.

### Section 4 — Decision Trail (Why — the product evolution narrative)

**This is new and is the most important section for understanding the project.**

Inspired by GitHub PR timeline — a chronological narrative of decisions, not a raw event dump.
Events are grouped into causation chains where detectable.

```
── 2026-03-05 ─────────────────────────────────────────────────────────

⚠ ESCALATION
  13:10  convergence_escalated
         edge: code↔unit_tests  ·  feature: REQ-F-GMON-003
         reason: "delta stuck at 2 for 5 iterations — agent cannot resolve ambiguity"
         escalated_to: human_review
         → 4 iterations tried before escalation

    ↳ 14:30  review_completed
             reviewer: user  ·  outcome: changes_requested
             "Test coverage threshold too strict for generated code — reduce to 80%"

    ↳ 15:00  spec_modified
             trigger_intent: INT-GMON-004
             delta: "REQ-F-PROF-002: reduced coverage threshold 90%→80% for generated assets"

── 2026-03-04 ─────────────────────────────────────────────────────────

🔍 FINDING → INTENT → SPEC CHANGE
  12:00  finding_raised (inward)
         "Monitor workspace itself lacked v2.5 data — self-monitoring gap"
         edge: design→code  ·  feature: REQ-F-GMON-001

    ↳ 12:05  intent_raised
             trigger: gap_found  ·  source: v2.5 gap analysis

    ↳ 12:10  spec_modified
             delta: "Added 17 new REQ keys for v2.5 alignment (sections 11-18)"
             trigger_intent: INT-GMON-004

    ↳ 12:15  feature_spawned
             REQ-F-GMON-001 → REQ-F-GMON-002  ·  reason: scope
             REQ-F-GMON-001 → REQ-F-GMON-003  ·  reason: scope

── 2026-02-28 ─────────────────────────────────────────────────────────

📦 RELEASE
  02:32  release_created  v1.0.0-alpha
         3 features included: REQ-F-GMON-001, REQ-F-GMON-002, REQ-F-GMON-003
```

**Entry types and their visual treatment:**

| Icon | Event Types | Why it matters |
|------|-------------|---------------|
| ⚠ ESCALATION | `convergence_escalated` + linked `review_completed` + linked `spec_modified` | Work stopped, needed human judgment |
| 🔍 FINDING | `finding_raised` + linked `intent_raised` + linked `spec_modified` + linked `feature_spawned` | Gap detected in spec/design/code |
| 👁 REVIEW | standalone `review_completed` (approved/deferred) | Human checkpoint |
| ✱ SPAWN | standalone `feature_spawned` / `feature_folded_back` | Scope change |
| ⚡ ENCODING | `encoding_escalated` | Effort/valence change |
| 📡 SIGNAL | `interoceptive_signal` / `exteroceptive_signal` + `affect_triage` | Sensory observation |
| 📦 RELEASE | `release_created` | Milestone |

**Causation chain construction:**
- `finding_raised` → look forward for `intent_raised` within 30 minutes → group them
- `intent_raised` → look forward for `spec_modified` with matching `trigger_intent` → group
- `spec_modified` → look forward for `feature_spawned` within 30 minutes → group
- `convergence_escalated` → look forward for `review_completed` on same (feature, edge) → group
- Items that don't link to anything are shown as standalone entries

**Filter bar (above the timeline):**
```
[All] [⚠ Escalations] [🔍 Findings] [👁 Reviews] [✱ Spawns] [📦 Releases]
```
Clicking a filter shows only that entry type — others are hidden.

**Replaces:** Consciousness Loop (partial) + Processing Phases (removed).

### Section 5 — Recent Activity (What happened — reflex stream)

A compact live event feed. NOT the same as the Decision Trail.
Only reflex.log events: `edge_started`, `iteration_completed`, `edge_converged`, `evaluator_detail`, `command_error`, `checkpoint_created`.

```
Time      Type                  Detail
12:49     edge_converged        requirements→design · REQ-F-GMON-004
12:49     iteration_completed   REQ-F-GMON-003:code↔tests (iter 2) — delta: 0 ✓
12:48     evaluator_detail      3 passed · 0 failed · 1 skipped
12:47     iteration_completed   REQ-F-GMON-003:code↔tests (iter 1) — delta: 2 ✗
12:46     edge_started          code↔unit_tests · REQ-F-GMON-003
```

**Formatting rules — NO raw dict repr ever:**

| Event Type | Detail Template |
|-----------|----------------|
| `edge_started` | `{edge}` · `{feature}` |
| `edge_converged` | `{edge}` · `{feature}` — `{convergence_type}` |
| `iteration_completed` | `{feature}:{edge}` (iter {n}) — delta: {delta} {✓|✗} |
| `evaluator_detail` | {passed} passed · {failed} failed · {skipped} skipped |
| `command_error` | ✗ {error, max 80 chars} |
| `checkpoint_created` | checkpoint at `{edge}` · `{feature}` |
| `health_checked` | {passed}/{total} checks — genesis_compliant: {bool} |
| `transaction_aborted` | ✗ `{feature}:{edge}` aborted — `{reason}` |

This section has a hard limit of 50 entries. "Show all →" links to the full event stream.

**Replaces:** Recent Events (existing) + TELEM Signals (removed as separate panel).

### Section 6 — Quality (Compliance + Traceability)

Three panels in a grid. Content unchanged from current implementation.

#### 6a — Protocol Compliance (v2.8)
Existing `_compliance.html` format is correct. Keep.

#### 6b — Constraint Dimensions
Existing `_dimensions.html` format is correct. Keep.
Highlight `unbound` mandatory constraints in red — they block design edge convergence.

#### 6c — Test Traceability
Existing `_traceability.html` format is correct. Keep.
The tree diagram (REQ keys → spec/code/test coverage) is the right format.

### Section 7 — Structure

Two panels: Vector Relationships + Feature → Module Map.
Existing formats are correct. Keep.

---

## Page: Edge Timeline (`/project/{id}/timeline`)

Answers: **What happened?** (EdgeRun history — trace view)

### Global time picker (same component as Project Dashboard)

### Tab 1 — Topology Trail (D3, existing REQ-F-GVIZ)
Structural projection: fixed node positions, arcs = EdgeRuns.
Encodes: path structure, feature colour, iteration effort (arc width), recency (opacity).

### Tab 2 — Lifecycle (D3, existing REQ-F-TSER)
Temporal projection: wall-clock X-axis, feature swimlanes, bar width = duration.
Encodes: sequence, gaps, parallelism.

**D3 zoom is LOCAL — does not change the global time picker.**
Optional: "Use as filter" button appears after zooming — reads D3 x-domain, fills time picker.

### Run Table (below D3 tabs)

Filterable table. Each row = one EdgeRun.

| Feature | Edge | Status | Iters | Final Δ | Duration | Started | Convergence |
|---------|------|--------|-------|---------|---------|---------|-------------|
| REQ-F-GMON-003 | code↔tests | ⚠ escalated | 10 | 2 | 3h | Mar 5 12:46 | escalated |
| REQ-F-GMON-004 | design→code | ✓ converged | 3 | 0 | 30m | Mar 4 05:54 | standard |

**Columns:**
- **Iters** — total `iterate()` cycles in this run
- **Final Δ** — delta at convergence (0 = clean pass; >0 = time-box or escalated)
- **Convergence** — standard | time_box_expired | escalated — shown as badge

Click any row → inline expansion showing:
```
Iteration history:
  iter 1  delta: 5  [3 passed · 2 failed · 0 skipped]  2026-03-05 12:47
           ✗ REQ-F-GMON-003: coverage_above_threshold — expected 90%, got 72%
           ✗ REQ-F-GMON-003: all_evaluators_passed — 2 failures
  iter 2  delta: 2  [4 passed · 1 failed · 0 skipped]  2026-03-05 13:02
           ✗ REQ-F-GMON-003: coverage_above_threshold — expected 90%, got 84%
  ...

Artifacts written:
  imp_fastapi/code/src/genesis_monitor/projections/features.py
  imp_fastapi/tests/test_features.py
```

Showing the delta curve visually inline (sparkline: `████▄▂▁▁` per iteration).

---

## Page: Feature Lineage (`/project/{id}/feature/{fid}`)

Answers: **What happened to this feature?** (one feature's full trace)

```
REQ-F-GMON-003 — v2.5 Alignment
Status: converged  ·  Profile: standard  ·  Parent: REQ-F-GMON-001  ·  Children: —

Spawned by: REQ-F-GMON-001 on 2026-03-04 · reason: scope
Spawned from finding: "Monitor workspace itself lacked v2.5 data"

Trajectory:
Edge            Status    Runs  Iters  Duration  Converged     Notes
requirements    ✓          1      1     1h        Mar 1         standard
design          ✓          1      1     2h        Mar 2         standard
code            ✓          3      8     4h        Mar 5         escalated on run 2
unit_tests      ✓          3      8     4h        Mar 5         co-evolving with code

Escalations on this feature:
  Mar 5 13:10  code↔tests  ·  "delta stuck at 2 for 5 iterations"  →  review_completed (changes_requested)

Requirements this feature contributes to:
  REQ-F-VREL-002, REQ-F-CDIM-002, REQ-F-PROF-002 (+ 7 more)
```

Per-edge run history (same expandable format as Run Table on Timeline page).

Linked artifacts for each converged edge (click → Artifact Viewer).

---

## Removed Panels

| Panel | Reason |
|-------|--------|
| Asset Graph (Mermaid) | Superseded by D3 Trail on Timeline page |
| Feature Vectors (card grid) | Superseded by Feature Matrix |
| Edge Convergence (panel) | Merged into Edge Summary |
| Edge Status (separate panel) | Merged into Edge Summary |
| TELEM Signals (separate panel) | Appear in Recent Activity feed |
| Processing Phases (separate panel) | Phase counters inline in Recent Activity footer |
| Consciousness Loop (separate panel) | Superseded by Decision Trail |
| Gantt / Timeline matrix (on project page) | Superseded by Feature Matrix (same data, better format) |
| Raw event dict repr | Always replaced by formatted template per event type |

---

## Implementation Priority

**Phase 1 — Fix broken rendering (bugs, no new features):**
1. Event formatting: replace raw `e.data | string | truncate(60)` with per-type templates
2. Duplicate column in Timeline/Gantt matrix: fix `code↔unit_tests` splitting into two columns
3. Feature Vectors: show title from feature vector; hide edges not in feature's profile
4. Feature names: REQ-F-NAV-001 etc. with no title → show feature_id only, no blank title

**Phase 2 — Consolidation (remove duplicates):**
5. Merge Edge Convergence + Edge Status → single Edge Summary
6. Remove Feature Vectors card grid (Feature Matrix is the replacement)
7. Remove Gantt/Timeline matrix (Feature Matrix is the replacement)
8. Replace Consciousness Loop + Processing Phases with Decision Trail

**Phase 3 — Time picker (replace scrubber):**
9. Global time picker component (presets + custom datetime inputs)
10. Wire `t_from`/`t_to` to EventIndex.timeline(since=, until=)
11. Live mode vs historical mode (SSE on/off)
12. Optional "Use as filter" bridge from D3 zoom to time picker

**Phase 4 — Decision Trail (new, the "why" view):**
13. Causation chain builder: group events by causal proximity (time + field matching)
14. Decision Trail template with collapsible groups
15. Filter bar (type buttons: Escalations/Findings/Reviews/Spawns/Releases)
16. Escalation + review detail: show iteration count before escalation, review outcome, spec change
