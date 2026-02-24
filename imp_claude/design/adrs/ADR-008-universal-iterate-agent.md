# ADR-008: Universal Iterate Agent

**Status**: Accepted
**Date**: 2026-02-19
**Deciders**: Methodology Author
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001

---

## Context

The Asset Graph Model defines software development as a directed cyclic graph with a universal iteration function. This means:

1. **Stages are not fundamental** — they are asset types in the graph
2. **The operation is always the same** — `iterate(Asset<Tn>, Context[], Evaluators(edge_type)) → Asset<Tn.k+1>`
3. **Behaviour is parameterised** — by edge type, evaluator configuration, and context
4. **Skills are evaluator/constructor logic** — they belong to edge configurations, not to stages

We need to decide how to implement this in Claude Code, where agents are markdown files.

### Options Considered

1. **Keep 7 agents, add parameterisation** — each agent reads edge config but retains stage persona
2. **Single iterate agent** — one markdown file, fully parameterised by edge config
3. **Meta-agent + generated agents** — a meta-agent generates per-edge agents dynamically

---

## Decision

**We will use a single iterate agent (`gen-iterate.md`) that reads edge parameterisation from YAML config files to determine its behaviour.**

The agent has no hard-coded knowledge of "stages". It reads:
- The edge type (which transition is being traversed)
- The evaluator configuration (which evaluators constitute `stable()`)
- The context (which constraints bound construction)
- The asset type schema (what the output must satisfy)

---

## Rationale

### Why Single Agent (vs 7 Agents)

**1. The model says so** — The Asset Graph Model defines one operation. Having 7 agents re-introduces the pipeline as an implementation artefact when the theory has eliminated it.

**2. Extensibility** — Adding a new asset type or edge requires only a YAML config change, not a new agent file. The graph is extensible without touching the engine.

**3. Consistency** — All edges get the same quality of implementation. With 7 agents, each had different prompting quality and different interpretations of iteration. One agent, one standard.

**4. Compression** — Single agent + YAML edge configs = 1 markdown file + ~5 small YAML files. Less surface area, easier to maintain.

**5. Self-consistency** — The methodology claims "one operation, parameterised per edge." The implementation should reflect this. Using 7 agents would be the implementation contradicting its own theory.

### Why Not Meta-Agent + Generated Agents

Dynamic agent generation adds complexity without benefit. Claude Code loads the agent markdown at invocation time. The iterate agent can read the edge config at that point — there's no need to pre-generate specialised agents.

---

## Consequences

### Positive

- **One file to maintain** — all iterate behaviour in one markdown file
- **Edge configs are data** — YAML files that can be versioned, diffed, composed
- **New edges are zero-code** — add a YAML config, the agent handles it
- **Theory-implementation alignment** — the code reflects the model

### Negative

- **Single large prompt** — the iterate agent markdown must handle all edge types; needs careful structuring to avoid confusion
- **Knowledge capture in edge configs** — Detailed per-domain knowledge must be captured in edge config guidance fields rather than agent prompts.
- **Debugging complexity** — when the agent behaves wrong on a specific edge, the issue could be in the agent prompt, the edge config, or the context. With 7 agents, the scope was narrower.

### Mitigation

- Structure the iterate agent with clear sections: "How You Work", "Evaluator Types", "Key Constraint"
- Edge configs include `guidance` fields with edge-specific prompting hints
- The `/gen-review` command provides human checkpoints for quality assurance

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3 (The Iteration Function), §4.6 (IntentEngine)
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §2.1 (Asset Graph Engine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-ITER-001, REQ-ITER-002
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (the iterate agent IS the IntentEngine; this ADR maps observer→evaluator→typed_output to iterate() invocations)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (sensory signals feed into iterate() as additional context)
