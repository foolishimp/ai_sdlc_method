# STRATEGY: Navigator-led consolidated widget specification

**Author**: codex
**Date**: 2026-03-13T01:48:24+11:00
**Addresses**: `projects/genesis_monitor`, `projects/genesis_navigator`, product-surface consolidation around widgets and presented information
**For**: all

## Summary
The two project specs should not continue as co-equal product definitions. `genesis_navigator` has the better architecture for the actual product purpose: a read-only navigation and decision surface over Genesis workspaces. `genesis_monitor` should be harvested as a source of additional projections and widgets, not as the governing information architecture.

The consolidation rule should be:
- `Navigator` defines the primary product structure
- `Monitor` contributes secondary and advanced widgets where they add decision value
- the spec should be rewritten around pages, widgets, and information payloads, not around implementation history or local naming drift

## Product Intent
The consolidated product should answer five user questions clearly:
1. What projects exist?
2. Where is this project right now?
3. What is broken or missing?
4. What should happen next?
5. What happened over time, and what is this feature?

That implies one primary product, not two divergent ones.

## Governing Product Model
The governing model should be the `Navigator` page structure:
- Project List
- Project Detail
  - Status
  - Gaps
  - Queue
  - History
- Feature Detail

This is already the cleanest user-facing decomposition in:
- `projects/genesis_navigator/imp_react_vite/frontend/src/pages/ProjectListPage.tsx`
- `projects/genesis_navigator/imp_react_vite/frontend/src/pages/ProjectDetailPage.tsx`
- `projects/genesis_navigator/imp_react_vite/frontend/src/pages/FeatureDetailPage.tsx`

The `Monitor` surface should be repriced as an extension library of deeper projections visible in:
- graph / convergence / edges / feature matrix
- traceability and feature-module map
- status panel
- timeline / edge traversal
- reviews / consensus
- workspace hierarchy
- telem signals

## Consolidated Widget Specification

### 1. Project List Page

**Purpose**: discover projects and choose a workspace to inspect.

**Required widgets**:
- Product header
- Refresh action
- Project list / cards

**Information each project row/card must present**:
- project name
- project path
- project state
- active feature count
- last event timestamp

**Primary source**: Navigator

**Monitor contribution**:
- optional bootloader badge
- optional workspace hierarchy hint if the project is parent/child in a CQRS-style tree

### 2. Project Detail Header

**Purpose**: maintain orientation inside one project.

**Required widgets**:
- back-to-projects action
- project identity block
- state badge
- refresh action
- tab selector

**Information required**:
- project name
- current project state
- project identifier / slug

**Primary source**: Navigator

**Monitor contribution**:
- optional design-tenant filter when multi-design tenancy is actually needed
- do not make tenant filtering part of MVP primary navigation

### 3. Status Tab

**Purpose**: answer “where am I now?”

**Required widgets**:
- project KPI cards
- feature trajectory list
- per-feature Hamiltonian / effort display

**Information required**:
- project state
- iterating feature count
- converged feature count
- converged edges / total edges
- for each feature:
  - feature ID
  - title
  - feature status
  - trajectory through edges
  - current edge
  - delta
  - Hamiltonian `H, T, V`

**Primary source**: Navigator

**Monitor contribution**:
- adopt Monitor’s denser edge and convergence projections where useful, but as subordinate visual encodings inside this tab
- the Monitor feature matrix is worth harvesting as an alternate status widget, not as the governing page architecture

### 4. Feature Detail Page

**Purpose**: answer “what is this feature and how is it progressing?”

**Required widgets**:
- feature identity card
- status badge
- Hamiltonian badge
- satisfies / REQ linkage widget
- trajectory widget
- acceptance criteria widget
- missing-feature guidance when spec exists but no vector exists

**Information required**:
- feature ID
- title
- feature status
- current edge
- `H, T, V`
- satisfies links
- ordered trajectory with edge status, iteration count, delta, converged timestamp
- acceptance criteria
- spawn guidance if vector missing

**Primary source**: Navigator

**Monitor contribution**:
- traceability drill-down
- feature-module map
- backing docs / ADR links

These should be extension panels on Feature Detail, not a separate mental model.

### 5. Gaps Tab

**Purpose**: answer “what is broken or missing?”

**Required widgets**:
- gap health summary header
- layered gap sections
- per-gap table rows

**Information required**:
- overall health signal
- required gap count
- layer breakdown
- per layer:
  - coverage percentage
  - gap count
  - whether the layer is blocking or advisory
- per gap:
  - REQ key
  - gap type
  - affected files where relevant

**Primary source**: Navigator

**Monitor contribution**:
- telem/sensory projections can enrich the advisory layer later
- do not let Monitor’s broader observability vocabulary bloat the core gap page

### 6. Queue Tab

**Purpose**: answer “what should happen next?”

**Required widgets**:
- queue summary
- ordered queue cards

**Information required**:
- queue item type
- severity
- associated feature if present
- delta if present
- reason / description
- gap keys where relevant
- failing checks where relevant
- suggested command or next action

**Primary source**: Navigator

**Monitor contribution**:
- Monitor’s richer event and convergence projections may feed queue ranking, but that belongs in computation, not in the visible IA

### 7. History Tab

**Purpose**: answer “what happened over time?”

**Required widgets**:
- run list
- current-session marker
- final-state badges
- run statistics
- timeline segment view
- event rows

**Information required**:
- run ID or “current session”
- final state
- event count
- edges traversed
- timestamp
- grouped event segments by feature / edge
- event types and local timestamps

**Primary source**: Navigator

**Monitor contribution**:
- Monitor’s edge traversal timeline is valuable and should be harvested as an advanced history mode
- the graph/timeline representation is an alternate visualization of the same history data, not a separate product area

## Advanced Widgets to Harvest from Monitor
These are valuable, but they should be explicitly secondary.

### A. Asset Graph Widget

**Use**: structural topology view of the project graph.

**Information**:
- nodes / assets
- transitions / edges
- state coloring

**Placement**: advanced Status subpanel or a dedicated advanced view, not the default first screen.

### B. Edge Convergence + Edge Status Tables

**Use**: dense operational view for power users.

**Information**:
- edge-level convergence state
- last delta / iteration curve
- convergence timestamps
- executor / convergence type later if needed

**Placement**: advanced Status subpanel.

### C. STATUS.md Panel

**Use**: compare rendered project state against materialized workspace status document.

**Information**:
- build schedule
- phase completion
- metrics

**Placement**: supporting panel under Status, not primary truth source.

### D. Traceability Widget

**Use**: evidence chain from feature to code/tests/telemetry.

**Information**:
- REQ key
- code files
- test files
- telemetry files

**Placement**: Feature Detail extension and possibly Gap Detail.

### E. Feature × Module Map

**Use**: architectural orientation for implemented features.

**Information**:
- feature to module coverage
- missing implementation links

**Placement**: Feature Detail extension.

### F. Reviews / Consensus Widget

**Use**: show formal review state when review machinery exists.

**Information**:
- open review sessions
- votes / quorum state
- comments / dispositions
- outcome

**Placement**: dedicated advanced review panel, not MVP project detail default.

### G. Workspace Hierarchy Widget

**Use**: parent/child workspace navigation for CQRS-style or nested workspaces.

**Information**:
- child workspace identity
- event count
- feature count
- converged count

**Placement**: project metadata or advanced navigation, not first-order status.

### H. TELEM / Sensory Signals Widget

**Use**: expose live signals and homeostatic observations.

**Information**:
- signal type
- severity
- source
- summary

**Placement**: advanced observability panel, or integrated into Gaps/Queue rather than standalone for most users.

## Widgets to Defer or Demote
These exist in Monitor, but they should not govern the consolidated spec.

- `Consciousness` timeline
- `Processing Phases / Regimes`
- protocol compliance as a top-level product area
- raw recent event feed as a primary panel

These may still be useful expert/debug surfaces, but they are not central user jobs. They describe the machinery more than they support navigation and action.

## Consolidated IA Decision
The consolidated IA should therefore be:

1. `Projects`
2. `Project Detail`
   - `Status`
   - `Gaps`
   - `Queue`
   - `History`
3. `Feature Detail`
4. `Advanced Views` (optional / progressive disclosure)
   - Graph
   - Edge Convergence
   - Traceability
   - Status.md
   - Reviews / Consensus
   - Workspace Hierarchy
   - Signals

This keeps the main UX simple while still allowing Monitor’s richer projections to survive as harvested modules.

## Specification Rewrite Rule
The rewritten spec should be organized around:
- pages
- widgets
- information contracts per widget
- read-only invariants
- progressive disclosure of advanced projections

It should not be organized around:
- which prototype introduced the idea
- separate Monitor vs Navigator product identities
- implementation-local route names
- internal projection jargon as first-order UX structure

## Recommended Action
1. Declare `genesis_navigator` the governing product architecture.
2. Reclassify `genesis_monitor` as a projection/widget harvest source.
3. Rewrite both project specs into one consolidated page-and-widget spec.
4. Keep only the Monitor widgets that directly improve the five core user questions.
5. Defer expert/debug surfaces into an explicit advanced layer instead of letting them dominate the product model.

The practical consequence is simple: the product should feel like Navigator with harvested Monitor depth, not like two competing interpretations of the same application.
