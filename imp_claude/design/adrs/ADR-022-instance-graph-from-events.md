# ADR-022: Instance Graph Derived from Events — Topology as Type System, Events as State

**Series**: imp_claude (Claude Code implementation decisions)
**Status**: Accepted
**Date**: 2026-03-03
**Scope**: Genesis Monitor graph display, graph_topology.yml role, feature vector positioning, zoom model
**Extends**: ADR-009 (Graph Topology as Configuration), ADR-019 (Orthogonal Projection Reliability), ADR-021 (Dual-Mode Traverse)

---

## Context

The Genesis Monitor currently renders the Asset Graph from `graph_topology.yml` — a static YAML file defining asset types and transitions. Node colouring comes from `STATUS.md`. Feature vectors are displayed in a separate table. Events are displayed in a separate table. These three views are disconnected.

This was acceptable as a first display approximation, but it produces a fundamental representation error: **the graph shown is the type schema, not the current system state.**

The spec's Asset Graph Model defines four primitives: Graph, Iterate, Evaluators, Spec+Context. The Graph primitive has two distinct aspects:

1. **Topology** — the set of admissible asset types and transitions (the schema). This is static — it defines what kinds of nodes and edges are *possible*.
2. **Instance** — the current state of the graph: which features exist, where each sits in the graph, which edges are active, which are converged. This is dynamic — it changes with every iteration.

The current monitor conflates these. `graph_topology.yml` is being used as both the schema and the display state.

### The Fractal Property

The spec's zoom model (PROJECTIONS_AND_INVARIANTS.md §3) states: the graph is self-similar at every zoom level. A feature vector at zoom level 1 is itself a sub-instantiation of the same topology. If REQ-F-ENGINE-001 spawns REQ-F-ENGINE-002, that spawn is zoom level 2 — the same asset types and transitions, narrower scope.

This fractal property means:
- **Zoom level 0**: the bootstrap graph (10-12 typed nodes) — methodology structure
- **Zoom level 1**: feature instance nodes, each positioned on the topology edge it currently occupies
- **Zoom level 2**: iteration history for a specific feature, check-level detail

Feature vectors are NOT separate from the graph. They ARE the graph at zoom level 1. The monitor presenting them in a separate table rather than as positioned nodes in the graph is an architectural error.

### The OpenLineage Connection

The OL event log records every state change in the instance graph:

| Event Type | Graph Operation |
|------------|----------------|
| `feature_spawned` | New node added at zoom level 1 |
| `edge_started` | Node moves to new edge position |
| `iteration_completed` | Node delta updated |
| `edge_converged` | Node transitions to converged state on this edge |
| `FEATURE_CONVERGED` | Node exits active graph (archived) |
| `spec_modified` | Topology schema versioned |

The event log is a complete, ordered record of graph mutations. The current instance graph is fully reconstructable from the event log by replaying these mutations in sequence. This is the **Event Sourcing** pattern applied to the asset graph — exactly what ADR-S-011 (OpenLineage) was designed for.

---

## Decision

**`graph_topology.yml` defines the TYPE SYSTEM — admissible node and edge types. The INSTANCE GRAPH — which nodes exist, where they sit, what their state is — is derived from the OpenLineage event log. The monitor renders the instance graph, not the topology schema. Zoom level 0 shows the topology shell; zoom level 1 overlays feature instances positioned on their current edge.**

### Topology as Type System

`graph_topology.yml` defines:
- `asset_types` — the kinds of nodes that can exist
- `transitions` — the kinds of edges that are admissible
- `profiles` — convergence parameterisation per context
- `constraint_dimensions` — what binds a graph instantiation to a context

Topology changes only when the **methodology evolves** — a new asset type is added, a new transition is defined, a profile is tuned. This is rare and always deliberate. The topology version (`2.8.0`) tracks methodology version.

### Instance Graph as Event Projection

The instance graph is a **projection over the event log**. It is computed at read time by the monitor's `parse_events()` function (or a new `project_instance_graph()` function):

```
events.jsonl → replay mutations → InstanceGraph
    feature_spawned(id, parent, zoom)  → node added
    edge_started(id, edge)             → node.current_edge = edge
    iteration_completed(id, delta)     → node.delta = delta
    edge_converged(id, edge)           → node.converged_edges.add(edge)
    FEATURE_CONVERGED(id)              → node.status = "archived"
```

The `InstanceGraph` is:
```python
@dataclass
class InstanceNode:
    feature_id: str         # REQ-F-*
    zoom_level: int         # 0 = topology, 1 = feature, 2 = sub-feature
    current_edge: str       # e.g. "code↔unit_tests"
    status: str             # pending | in_progress | converged | archived
    delta: int              # last known delta
    parent_id: str | None   # for zoom level 2+

@dataclass
class InstanceGraph:
    topology: GraphTopology             # the type system
    nodes: list[InstanceNode]           # current live instances
    as_of: datetime                     # event log watermark
```

### Zoom Model in the Monitor

The monitor renders three zoom levels:

**Zoom 0 — Topology Shell** (current behaviour, kept):
```
intent → requirements → feature_decomposition → design → code ↔ unit_tests → ...
```
Nodes coloured by whether any feature is active on that edge. This is the methodology structure view.

**Zoom 1 — Feature Instance Graph** (new):
Feature nodes are **overlaid** on the topology shell. Each feature node is positioned at its current edge. Multiple features on the same edge are shown as a count badge or small sub-nodes.

```
design → [REQ-F-ENGINE-001 ✓] → code ↔ [REQ-F-ROBUST-001 ⟳] unit_tests → ...
                                          [REQ-F-FP-001 ✓]
```

Clicking a feature node drills to zoom level 2.

**Zoom 2 — Iteration Detail** (new):
Shows the iteration history for a specific feature on a specific edge — delta sequence, check results, event trail.

### Topology Version vs Instance Version

Two versioning concerns that were previously conflated:

| Concern | Source | Version field |
|---------|--------|---------------|
| **Topology version** | `graph_topology.yml` | `graph_properties.version` (e.g. `2.8.0`) — changes when methodology structure changes |
| **Instance state version** | Last event timestamp | `events.jsonl` watermark — changes with every event |

The monitor must track both:
- Topology version: to warn when workspace topology is stale vs plugin reference
- Instance watermark: to display "last updated" correctly and detect stale projections

### Workspace Topology Sync

`gen-setup.py` (and the SessionStart hook) should check workspace topology version against the plugin reference:

```bash
# SessionStart health check addition:
WORKSPACE_VER=$(grep "version:" .ai-workspace/graph/graph_topology.yml | head -1 | cut -d'"' -f2)
PLUGIN_VER=$(grep "version:" $CLAUDE_PLUGIN_ROOT/config/graph_topology.yml | head -1 | cut -d'"' -f2)
if [ "$WORKSPACE_VER" != "$PLUGIN_VER" ]; then
  echo "⚠ graph_topology.yml stale: workspace=$WORKSPACE_VER plugin=$PLUGIN_VER"
  echo "  Run: cp $CLAUDE_PLUGIN_ROOT/config/graph_topology.yml .ai-workspace/graph/graph_topology.yml"
fi
```

---

## Consequences

**Positive:**
- **Correct representation**: the monitor shows what IS, not what COULD BE. Feature vectors appear in the graph as first-class positioned nodes, not a separate list.
- **Fractal consistency**: zoom levels 0/1/2 all use the same rendering model — topology shell + instance overlay. Sub-features at zoom 2 are structurally identical to features at zoom 1.
- **Event sourcing integrity**: the instance graph is fully derived from the append-only event log. No separate mutable state. Replay from any point in the log to see historical graph state.
- **Topology evolution decoupled from instance evolution**: adding a new feature doesn't require updating `graph_topology.yml`. Updating `graph_topology.yml` doesn't invalidate existing feature instances.
- **Version drift detectable**: topology version mismatch is now a first-class observable (SessionStart health check).

**Negative / Trade-offs:**
- **Monitor complexity**: building the instance graph projection from events is more work than reading a static file. The `project_instance_graph()` function must correctly replay mutations in order.
- **Event log dependency**: if the event log is corrupt or missing, the instance graph cannot be reconstructed. Mitigated by the existing `workspace_state.validate_events()` function and health checks.
- **Performance**: replaying events on every page load is O(n events). Mitigated by caching the projection with the event log watermark as the cache key — invalidate only when new events arrive.

### Design-Layer Graph Projections

The zoom model is not only about depth (feature → sub-feature). The **design phase** produces assets that are themselves graphs — with different structure than the linear bootstrap topology. These emerge naturally from the `feature_decomposition→design→module_decomposition→basis_projections` edges and are renderable using the same instance-graph-from-events model.

#### The Three Design-Layer Graphs

**Graph A — Feature × Module bipartite map (N:N)**

The `design→module_decomposition` traversal assigns modules to features. A feature may be implemented by multiple modules; a module may serve multiple features. This is a bipartite graph:

```
REQ-F-ENGINE-001 ──┬── engine.py
                   └── dispatch.py

REQ-F-EVAL-001  ──┬── fd_evaluate.py
                   ├── fp_evaluate.py
                   └── engine.py        ← shared module
```

Projection query: `SELECT feature, module FROM module_assigned events`

**Graph B — Module dependency DAG**

Modules depend on other modules. The `module_decomposition` asset records these explicitly. This is a directed acyclic graph (enforced — cycles are a convergence failure):

```
engine.py → fd_evaluate.py → fd_emit.py
engine.py → fp_evaluate.py → fp_subprocess.py
dispatch.py → engine.py
```

Projection query: `SELECT module, depends_on FROM module_dependency_declared events`

**Graph C — Basis projection graph (interface contracts)**

The `basis_projections` asset type records the interface contracts between modules — what each module exposes and consumes. This graph is the boundary surface between modules:

```
engine.py  exposes: iterate_edge(edge, config) → IterationRecord
fd_emit.py exposes: emit_event(event_type, data) → None
           consumes: events.jsonl (file path from workspace)
```

Projection query: `SELECT module, interface FROM basis_projection_declared events`

#### Unified Zoom Model

```
Zoom 0  Topology shell         — methodology structure (10-12 typed nodes)
Zoom 1  Feature instance graph — REQ-F-* nodes positioned on current edge
Zoom 2  Feature×Module map     — bipartite graph, features left / modules right
Zoom 3  Module dependency DAG  — directed graph, modules → modules
Zoom 4  Basis projections      — interface contract graph, modules → interfaces
```

Each zoom level is a **different projection over the same event log** — not a different data model. The event types that drive each projection:

| Zoom | Driving event types |
|------|---------------------|
| 0 | topology.yml (static) |
| 1 | `feature_spawned`, `edge_started`, `edge_converged` |
| 2 | `module_assigned` (emitted during `design→module_decomposition`) |
| 3 | `module_dependency_declared` |
| 4 | `basis_projection_declared` |

#### Rendering Note

Zoom 2-4 require event types (`module_assigned`, `module_dependency_declared`, `basis_projection_declared`) that are not yet in the Claude event schema. These should be added when the `design→module_decomposition` and `module_decomposition→basis_projections` edges are implemented. The monitor can render placeholder graphs until those events exist — showing the feature→module structure derived from REQ key tagging in code files (`# Implements: REQ-F-*`) as an approximation.

### Implementation Status

| Gap | Status | Notes |
|-----|--------|-------|
| **`project_instance_graph(events) → InstanceGraph`** | Not started | New projection function in genesis_monitor |
| **Zoom 0→1: timeline matrix table** | **[IMPLEMENTED 2026-03-03]** | Replaces Mermaid Gantt; `build_feature_matrix()` in `projections/gantt.py`; HTML matrix table in `_gantt.html`; feature × edge with hierarchy, status symbols, iteration count |
| **Zoom 1 graph overlay** in `graph.py` | Not started | Position feature nodes on topology edges |
| **Zoom 2: Feature×Module bipartite renderer** | **[IMPLEMENTED 2026-03-03]** | `build_feature_module_map()` in `projections/feature_module_map.py`; uses REQ tag scan (`TraceabilityReport.code_coverage`) as approximation pending `module_assigned` events; renders in `_feature_module_map.html`; gap detection (untraced REQ keys highlighted red) |
| **Zoom 3 DAG renderer** | Not started | Module dependency graph from `module_dependency_declared` events |
| **Zoom controls** in monitor UI | Not started | Click topology node → zoom 1; click feature node → zoom 2 |
| **Event schema additions** | Not started | `module_assigned`, `module_dependency_declared`, `basis_projection_declared` |
| **SessionStart topology version check** | Not started | Warn when workspace `graph_topology.yml` stale vs plugin |

### Zoom 2 Approximation Note (2026-03-03)

The Feature×Module bipartite renderer uses `TraceabilityReport.code_coverage` (derived from `# Implements: REQ-*` file scans) as an approximation for the eventual `module_assigned` event stream. This produces useful output now:

- **Source**: feature vector `requirements[]` + `code_coverage[req_key] → files`
- **Limitation**: files, not module boundaries — a file may implement multiple modules; a module may span files
- **Gap detection**: REQ keys in the feature vector that have no implementing file are flagged red — these are the same gaps `/gen-gaps` Layer 1 would report

When `module_assigned` events are added (Zoom 2 full implementation), `build_feature_module_map()` should be updated to prefer event-derived module assignments over file-scan approximations.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md) §2 (Graph primitive — topology vs instance)
- [PROJECTIONS_AND_INVARIANTS.md](../../../specification/core/PROJECTIONS_AND_INVARIANTS.md) §3 (Zoom model — self-similar at every level)
- [ADR-S-011](../../specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md) — OpenLineage as the instance graph mutation log
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — topology as configuration (this ADR splits that into type system vs instance)
- [ADR-019](ADR-019-orthogonal-projection-reliability.md) — Level 4 event reliability; instance graph reconstruction depends on reliable event emission
- [ADR-021](ADR-021-dual-mode-traverse.md) — engine emits Level 4 events; these are the instance graph mutations
- `genesis_monitor/projections/graph.py` — current renderer (reads topology only; zoom 1 overlay to be added)
- `genesis_monitor/parsers/features.py` — feature vector parser (currently builds instance nodes from yml, not events)
