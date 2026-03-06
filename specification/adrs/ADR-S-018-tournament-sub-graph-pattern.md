# ADR-S-018: Tournament Sub-Graph Pattern

**Status**: Ratified
**Date**: 2026-03-07
**Author**: Gemini (derived from Codex review)
**Applies To**: Formal System (AI SDLC Asset Graph Model v3.0)

## Context

As the AI SDLC scales, we encounter scenarios where a single agent's execution may produce suboptimal results due to path dependence or probabilistic hallucination. To counteract this, we introduced the concept of a "Tournament Pattern": spawning multiple parallel iterations (often across different agent models or configurations) for a given edge, evaluating the candidates against each other, and merging the best result back into the main feature vector.

Initially, this was envisioned as an internal parameter of the `design → code` edge (e.g., configuring `fan_out: 3`). However, as pointed out by Codex (Codex item 7) and refined by Gemini, hiding this orchestration inside a single edge breaks the formal properties of the Asset Graph:
1. **Transaction Boundaries**: Overloading an edge obscures the `START` and `COMPLETE` state-boundary events for the spawned tasks.
2. **Provenance**: If multiple children produce candidates and a composite is merged, a single edge transition cannot mathematically represent the complex fold-back provenance.
3. **Failure Isolation**: If one child fails, the whole edge would fail or require complex internal retry logic.

## Decision

We will model the **Tournament Pattern** as an explicit structural sub-graph in the topology rather than as parameterization on a single edge.

When a feature vector enters a competitive traversal, it traverses the following explicit nodes:
```text
parent_state → parallel_spawn → tournament_arbitration → tournament_merge → next_state
```
*(e.g., `design → parallel_spawn → tournament_arbitration → tournament_merge → code`)*

### 1. New Topological Nodes

- **`parallel_spawn`**: The transaction boundary where the parent feature suspends its linear progression and explicitly emits `feature_spawned` events for $N$ child vectors.
- **`tournament_arbitration`**: The node where parallel child outputs are gathered and evaluated (via F_P or F_H). This node is structurally responsible for candidate ranking.
- **`tournament_merge`**: The node where the selected candidate(s) are merged. If a composite asset is built (e.g., cherry-picking features from two candidates), the output is materialized here.

*(Note: `tournament_commit` is implicitly the `COMPLETE` event exiting the `tournament_merge` node).*

### 2. Causal Links and OpenLineage Alignment

To ensure unbroken mathematical traceability, the lineage of spawned tournaments MUST adhere to the OpenLineage standard for parent/child runs:
- Child vectors spawned during `parallel_spawn` MUST include the `run.facets.parent` facet, referencing the `runId` of the parent tournament edge.
- The system must not rely on informal `parentRunId` string fields outside the standardized OpenLineage facet schema.

### 3. Merge Provenance Fields

The `COMPLETE` event emitted by the `tournament_merge` edge MUST contain explicit **merge provenance**.
The event payload must include a `merge_provenance` facet detailing:
- The list of evaluated child `runId`s.
- The `content_hash` of each child candidate.
- The final selection policy used (e.g., `single_winner`, `composite`).
- The resulting output hash of the merged parent asset.

## Consequences

- **Positive**: Clean transaction semantics. The engine's inner loop remains simple (it just executes edges); orchestration is lifted to the graph topology level.
- **Positive**: Auditable fold-back semantics. Every composite decision is structurally recorded in the event stream.
- **Negative**: The `graph_topology.yml` becomes more complex, requiring specific standard profiles to explicitly map through or bypass these nodes depending on configuration.

## Implementation Requirements

- **REQ-GRAPH-004 (Tournament Topology)**: The specification and standard `graph_topology.yml` must include `parallel_spawn`, `tournament_arbitration`, and `tournament_merge` as valid asset types or states.
- **REQ-EVENT-005 (Parent Causal Links)**: All spawn events must use the OpenLineage `run.facets.parent` standard.
- **REQ-EVENT-006 (Merge Provenance)**: Tournament merge completion events must explicitly list child output hashes and the selection policy.