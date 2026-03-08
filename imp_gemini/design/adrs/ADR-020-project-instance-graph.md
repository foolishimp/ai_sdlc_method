# ADR-020: Project Instance Graph Implementation in imp_gemini

**Series**: Implementation (imp_gemini)
**Status**: Proposed
**Date**: 2026-03-08
**Refers to**: ADR-S-021

--- 

## Context

As specified in ADR-S-021, the system requires a formal `ProjectInstanceGraph` to track the actual execution trajectory of intent vectors, distinct from the abstract methodology template.

## Decision

### ProjectInstanceGraph as an In-Memory Model

In `imp_gemini`, the `VectorRegistry` (previously ADR-007) is extended to maintain a dynamic directed graph of all active and converged intent vectors.

1.  **Node Generation**: Every `gemini -s` (spawn) or gap detection event adds a new node to the project graph.
2.  **Edge Mapping**: Edges represent causal dependency (parent-to-child) and resolution dependency (intent-to-requirements).
3.  **Visualization**: The `gemini -g` (graph) command will project this instance graph into a Mermaid diagram, allowing the user to see the "traversed territory" of the project in real-time.

## Operational Implementation

- **Projector Service**: A background service that reconstructs the instance graph from the `events.jsonl` stream.
- **Graph Schema**: Nodes carry metadata (status, profile, resolution level) and edges carry the transition type (spawn, refine, fold-back).

## Consequences

- **Positive**: Real-time visibility into the project's trajectory. Clear separation between the methodology "map" and the project "territory."
- **Negative**: Graph reconstruction overhead on very large projects (mitigated by snapshotting).
