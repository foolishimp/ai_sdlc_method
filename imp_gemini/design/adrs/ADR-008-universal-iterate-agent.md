# ADR-008: Universal Iterate Agent

**Status**: Accepted
**Date**: 2026-02-19
**Deciders**: Methodology Author
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001

---

## Context

The methodology requires a robust mechanism for artifact construction across all edges of the asset graph. Traditional stage-specific agents are too rigid for a graph-based SDLC.

We need a single, universal operation—`iterate()`—that can be parameterised to handle any transition in the graph, regardless of the asset types involved.

The Asset Graph Model defines one operation: `iterate(Asset<Tn>, Context[], Evaluators(edge_type)) → Asset<Tn.k+1>`.

We need to decide how to implement this in a CLI-native environment.

### Options Considered

1. **Multiple agents** — separate agents for requirements, design, code, etc.
2. **Single iterate agent** — one agent markdown file, fully parameterised by edge config.
3. **Meta-agent + generated agents** — a meta-agent generates per-edge agents dynamically.

---

## Decision

**We will use a single iterate agent (`gen-iterate.md`) that reads edge parameterisation from YAML config files to determine its behaviour.**

The agent has no hard-coded knowledge of specific SDLC "stages". It reads:
- The edge type (which transition is being traversed)
- The evaluator configuration (which evaluators constitute `stable()`)
- The context (which constraints bound construction)
- The asset type schema (what the output must satisfy)

---

## Rationale

### Why Single Agent

**1. Theoretical Alignment** — The Asset Graph Model defines one operation. The implementation should reflect this directly to maintain conceptual integrity.

**2. Extensibility** — Adding a new asset type or edge requires only a YAML config change, not a new agent persona. The graph is extensible without touching the engine.

**3. Consistency** — All edges benefit from the same high-quality iteration logic. A single agent maintains a consistent understanding of the overall project state and the formal system's invariants.

**4. Compression** — Significant reduction in prompting surface area. One agent and a set of small YAML files are easier to maintain and port across platforms.

---

## Consequences

### Positive

- **One file to maintain** — all iterate behaviour is consolidated.
- **Edge configs are data** — YAML files can be versioned, diffed, and composed.
- **New edges are zero-code** — adding a YAML config is the only requirement for new transitions.
- **Theory-implementation alignment** — the implementation is a direct mapping of the formal model.

### Negative

- **Single large prompt** — the iterate agent markdown must handle multiple SDLC roles; it requires careful structuring to avoid ambiguity.
- **Expertise encoding** — domain-specific knowledge (e.g., requirements extraction) must be captured in edge configs rather than agent personas.
- **Debugging complexity** — issues on a specific edge may stem from the agent prompt, the edge config, or the context.

### Mitigation

- Structure the iterate agent with clear, functional sections: "How You Work", "Evaluator Types", "Key Constraint".
- Edge configs include `guidance` fields for edge-specific prompting hints.
- The `/gen-review` command provides human checkpoints for quality assurance.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3 (The Iteration Function)
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §2.1 (Asset Graph Engine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-ITER-001, REQ-ITER-002
