# ADR-009: Graph Topology as Configuration

**Status**: Accepted
**Date**: 2026-02-19
**Deciders**: Methodology Author
**Requirements**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-CTX-001

---

## Context

The v2.1 Asset Graph Model defines software development as a directed cyclic graph of typed assets connected by admissible transitions. The graph topology — which asset types exist and which transitions are allowed — is fundamental to the methodology.

The graph topology must be explicitly represented as configuration, not implicit in agent implementations.

We need to decide how to represent the graph topology in the Claude Code implementation.

### Options Considered

1. **Hard-coded in agent markdown** — describe the graph inline in the iterate agent prompt
2. **YAML configuration files** — separate files for asset types and transitions, loaded by the engine
3. **Code-based registry** — Python/TypeScript code defining types and transitions programmatically
4. **JSON Schema** — formal schema definitions with validation

---

## Decision

**We will represent the graph topology as YAML configuration files in the workspace Context[] store.**

Specifically:
- `asset_types.yml` — defines each asset type with schema and Markov criteria
- `transitions.yml` — defines admissible transitions with evaluator and constructor specifications
- `edges/*.yml` — per-edge parameterisation configs (TDD, BDD, ADR generation, code tagging)

These files live in `.ai-workspace/graph/` and are part of Context[]. The iterate agent reads them at invocation time.

---

## Rationale

### Why YAML Configuration (vs Hard-Coded)

**1. Graph topology IS context** — The Asset Graph Model (§5) explicitly states that the graph topology is itself an element of Context[]. Representing it as YAML config files that live in the context store is the correct implementation of this insight.

**2. Extensibility without code changes** — Adding a new asset type (e.g., `api_spec`) or a new transition (e.g., `api_spec→code`) requires only YAML edits. No agent markdown changes, no code changes. This satisfies REQ-GRAPH-003 (extensible graph).

**3. Context hierarchy** — The federated context model means graph topology can be composed: corporate defines base types, team adds domain-specific types, project customises transitions. YAML files compose naturally via deep merge.

**4. Diffable and versionable** — YAML files work with git. Teams can review graph topology changes in pull requests. The context manifest (REQ-INTENT-004) can hash the topology files for reproducibility.

**5. Readable by the iterate agent** — Claude Code agents read files. YAML is more readable to the LLM than JSON Schema or code. The agent can parse and reason about the topology to decide which transitions are admissible from the current state.

### Why Not Code-Based Registry

Claude Code's implementation is markdown-first. The agents are markdown files, the commands are markdown files. Introducing a code-based registry would require a runtime environment (Python/Node.js), breaking the "just files" principle. YAML configs maintain the no-runtime-dependency model.

### Why Not JSON Schema

JSON Schema is more precise but less readable for LLMs. The iterate agent needs to reason about asset types and transitions — YAML with comments is more effective for this purpose. Schema validation can be added as a deterministic evaluator if formal validation is needed later.

---

## Consequences

### Positive

- **Graph is inspectable** — developers can read the YAML to understand the project's SDLC topology
- **Graph is configurable** — teams can customise without forking the plugin
- **Graph is composable** — context hierarchy applies to topology
- **Graph is versionable** — git tracks topology changes
- **No runtime dependency** — just files, consistent with the markdown-first principle

### Negative

- **No runtime validation** — YAML files can have syntax errors or invalid references (e.g., a transition referencing a non-existent asset type). Validation depends on the iterate agent detecting issues at invocation time.
- **LLM parsing risk** — the iterate agent must correctly parse YAML. Malformed configs could cause subtle behavioural errors.
- **No type safety** — unlike a code-based registry, there's no compile-time guarantee that the topology is well-formed.

### Mitigation

- `/gen-init` generates valid default topology from the plugin's templates
- The iterate agent includes instructions to validate topology before proceeding
- A deterministic evaluator can be added for topology validation (check referential integrity)

---

## Default Topology

The plugin ships with a default graph topology representing the standard SDLC:

```
intent → requirements → design → code ↔ unit_tests
                          │
                          ├──→ uat_tests
                          └──→ test_cases

code → cicd → running_system → telemetry → intent (feedback loop)
```

Projects can extend, modify, or simplify this topology via their workspace YAML.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §2 (The Asset Graph), §4.6 (IntentEngine), §5 (Constraint Surface)
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §2.1 (Asset Type Registry, Admissible Transitions)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (edge configs encode ambiguity classification thresholds: `max_iterations`, `stuck_threshold`, evaluator composition)
