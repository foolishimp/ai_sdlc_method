# ADR-S-021: Project Instance Graph — Topology as Schema, Events as State

**Status**: Accepted
**Date**: 2026-03-07
**Author**: Gemini (derived from ADR-022)
**Requirements**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-UX-003
**Extends**: ADR-S-011 (OpenLineage), ADR-S-012 (Event Stream)

## Context

The Asset Graph Model defines two distinct aspects of the graph primitive:
1. **Topology**: The static schema of admissible asset types and transitions (e.g., `graph_topology.yml`).
2. **Instance**: The dynamic state of features traversing that topology.

Traditionally, methodology tools have conflated these, often rendering a static "process diagram" that does not reflect the live state of the project.

## Decision

The methodology formally adopts an **Event-Sourced Instance Graph** model. 

1. **Topology as Type System**: The `graph_topology.yml` (or equivalent) defines the "type system" — what nodes and edges are possible.
2. **Instance as Event Projection**: The "Instance Graph" — which features exist, where they sit, and their convergence status — is a **projection over the OpenLineage event log**.

### 1. Instance Node Schema

An Instance Node is the unit of the dynamic graph:
- `feature_id`: The REQ-F-* identifier.
- `current_edge`: The edge the feature is currently traversing.
- `status`: `pending | in_progress | converged | archived`.
- `delta`: The current failing check count (free energy).
- `converged_edges`: The set of edges this feature has already stabilized.

### 2. Projection Logic

The instance state is reconstructed by replaying the event stream:
- `feature_spawned` → Add node.
- `edge_started` → Update `current_edge`, set status to `in_progress`.
- `iteration_completed` → Update `delta`.
- `edge_converged` → Add to `converged_edges`.
- Derived terminal condition: when `converged_edges` covers all required edges in the feature's active profile → set status to `converged`. This is a projection, not a separate event — the terminal state is computed from `edge_converged` events against the profile's edge list.

### 3. Visualisation (The Zoom Model)

An observer (monitor) should render the following zoom levels:
- **Zoom 0 (Topology Shell)**: The structural methodology graph.
- **Zoom 1 (Feature Overlay)**: Feature instance nodes overlaid on their current topology edges.
- **Zoom 2 (Iteration Detail)**: The internal trajectory of a single feature.

## Consequences

- **Integrity**: The graph state is always consistent with the event ledger.
- **Auditability**: By replaying the ledger to any timestamp, the system can render the graph as it appeared at any point in the past.
- **Decoupling**: Adding features or traversing edges does not require modifying the static topology schema.
