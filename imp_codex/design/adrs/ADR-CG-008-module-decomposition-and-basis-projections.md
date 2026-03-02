# ADR-CG-008: Promote Module Decomposition and Basis Projections to First-Class Graph Nodes

**Status**: Accepted  
**Date**: 2026-03-03  
**Applies To**: `config/graph_topology.yml`, `config/edge_params/*.yml`, `code/agents`, `code/commands`

---

## Context

The plugin previously treated the build path from Design to Code as a single edge (`design→code`), with any sub-structure expressed only as zoomed sub-steps. This implicit handling caused:

1. Parallelism bottlenecks — multiple agents touching the same files without explicit module boundaries.
2. Weak build-architecture traceability — no explicit convergence criteria for module boundaries and inter-module contracts.
3. Missing projection artifacts — feature→module intersections (basis projections) were undocumented, making scope isolation and sequencing difficult.

The specification (AI_SDLC_ASSET_GRAPH_MODEL v2.8.0, §2.1/§6.7) and ADR‑S‑007 promote `Module Decomposition` and `Basis Projections` to explicit nodes.

## Decision

Adopt explicit nodes and edges in the graph package:

```
requirements→feature_decomp→design→module_decomp→basis_projections→code
```

### Artifacts and Convergence Criteria

Module Decomposition produces:
- Module map (architecture→packages mapping)
- Dependency DAG (acyclic) aligned with design constraints
- Interface contracts (public APIs between modules)

Basis Projections produce:
- Projected intent per (feature×module)
- Local interface subset required by the projection
- Stub/mock specifications for dependent modules

Markov criteria:
- Module DAG is acyclic; every design component mapped to ≥1 module; inter-module contracts defined.
- For each MVP feature, all required modules have projections; the sum of projections equals the feature intent; projections respect module contracts.

## Consequences

Positive:
- Orthogonal parallelism bounded by module interfaces.
- Explicit, evaluable build architecture with traceable decisions.
- Clearer sequencing via projection priorities.

Trade-offs:
- Two extra nodes increase ceremony for trivial projects; profiles may collapse them (`poc`, `spike`).

## Implementation Notes

Plugin work (subsequent changes):
- Add asset types: `feature_decomp`, `module_decomp`, `basis_projections` to `graph_topology.yml`.
- Add 5 transitions and corresponding `edge_params/*.yml` parameterisations.
- Update `agent_roles.yml` `converge_edges` to authorise new edges.
- Extend feature vector template trajectory to record new nodes.

## References

- Spec: AI_SDLC_ASSET_GRAPH_MODEL §2.1, §6.7  
- ADR‑S‑006: Feature Decomposition node  
- ADR‑S‑007: Module Decomposition & Basis Projections  
- FEATURE_VECTORS.md (updated trajectories and coverage)

