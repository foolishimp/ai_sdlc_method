# ADR-008: Universal Iterate Agent

**Status**: Accepted
**Date**: 2026-02-19
**Deciders**: Methodology Author
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001
**Supersedes**: ADR-003 (Agents for Stage Personas), ADR-004 (Skills for Reusable Capabilities), ADR-005 (Iterative Refinement Feedback Loops)

---

## Context

The v1.x design (ADR-003) used 7 separate agent markdown files — one per pipeline stage (requirements, design, tasks, code, system-test, uat, runtime-feedback). Each agent had a hard-coded persona, fixed inputs/outputs, and stage-specific skills (ADR-004). The iterative refinement loops (ADR-005) were per-stage patterns bolted onto the pipeline.

The v2.1 Asset Graph Model replaces the 7-stage pipeline with a directed cyclic graph and a universal iteration function. This means:

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

**4. Compression** — v1.x had 7 agents + 11 skills = ~18 markdown files of prompting. v2.1 has 1 agent + edge configs = 1 markdown file + ~5 small YAML files. Less surface area, easier to maintain.

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
- **Loss of stage-specific expertise** — v1.x agents had detailed per-stage prompts (e.g., the requirements agent had 200 lines of prompting for requirements extraction). This knowledge must be captured in edge configs instead.
- **Debugging complexity** — when the agent behaves wrong on a specific edge, the issue could be in the agent prompt, the edge config, or the context. With 7 agents, the scope was narrower.

### Mitigation

- Structure the iterate agent with clear sections: "How You Work", "Evaluator Types", "Key Constraint"
- Edge configs include `guidance` fields with edge-specific prompting hints
- The `/gen-review` command provides human checkpoints for quality assurance

---

## Relation to Superseded ADRs

| Superseded ADR | What It Specified | Where It Goes in v2.1 |
|---------------|-------------------|----------------------|
| ADR-003 (Stage Personas) | 7 agent markdown files with per-stage personas | 1 iterate agent, personas encoded in edge configs |
| ADR-004 (Reusable Skills) | 11 skills (extraction, merging, etc.) | Evaluator/constructor logic in edge parameterisations |
| ADR-005 (Feedback Loops) | Per-stage iteration patterns | Inherent in iterate() — the operation IS iteration |

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3 (The Iteration Function), §4.6 (IntentEngine)
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §2.1 (Asset Graph Engine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-ITER-001, REQ-ITER-002
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (the iterate agent IS the IntentEngine; this ADR maps observer→evaluator→typed_output to iterate() invocations)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (sensory signals feed into iterate() as additional context)
