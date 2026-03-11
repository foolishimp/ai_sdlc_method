# ADR-S-035: Genesis DSL — Topology Language Over Static File Structure

**Status**: PROPOSAL
**Date**: 2026-03-11
**Authors**: foolishimp
**Scope**: Specification-level — applies to all Genesis implementations

---

## Context

Genesis currently packages its methodology as a bundle of static files:

```
config/
  graph_topology.yml       — fixed graph for all projects
  edge_params/*.yml        — per-edge evaluator configuration
  profiles/*.yml           — skip-lists over the fixed graph
  intentengine_config.yml  — named compositions as YAML strings
  project_constraints.yml  — project-specific values
.ai-workspace/             — runtime state (events, vectors, artifacts)
```

This structure has three compounding problems:

**1. Topology is not parameterised.**
`graph_topology.yml` is a global definition shared by all projects regardless of domain. A regulated fintech team, a mobile app team, and a data pipeline team are forced into the same graph shape. Profiles are skip-lists — they can omit edges but cannot add domain-specific ones, compose graphs, or express inheritance.

**2. The methodology and the project are conflated.**
The same file bundle holds both "how to run Genesis" (methodology) and "what this specific project needs" (values). Changing the methodology means editing the same files that hold project state. There is no clean separation between the *definition* of a methodology and an *instantiation* of one.

**3. Higher-order composition is not expressible.**
Named compositions (ADR-S-026) exist as strings in YAML — they are not executable. Sequences, parallel edges, retry policies, time-boxes, and conditional graph branches cannot be expressed without modifying the Python engine. The current structure has no way to compose operators at the methodology level.

The analogy to **Helm** is precise: Helm solved the same problem for Kubernetes by separating *charts* (parameterisable templates defining what can be deployed) from *values* (project-specific configuration) from *releases* (deployed runtime state). Before Helm, Kubernetes users maintained static YAML manifests per environment. Genesis currently operates at the pre-Helm level.

---

## Decision

**Genesis packages become DSL programs, not file bundles.**

A new domain-specific language — the **Genesis Topology Language (GTL)** — replaces the static configuration files as the primary authoring surface. The static YAML files become the *compiled output* of a GTL program; they are not hand-authored.

The three-layer separation becomes:

| Layer | What it is | Authored as |
|-------|-----------|-------------|
| **Methodology** (`genesis.gen`) | Graph topology + operator definitions + compositions | GTL program |
| **Project** (`constraints.yml`) | Project-specific values injected into the methodology | YAML (unchanged) |
| **Runtime** (`.ai-workspace/`) | Event log + feature vectors + artifacts | Unchanged |

This maps to Helm's chart / values / release distinction exactly.

---

## The Genesis Topology Language

GTL is a **live topology language**, not a template language. The distinction matters: Helm templates compile to static manifests that are then applied. A GTL program defines a graph that remains the live topology during engine execution — the DSL is not compiled away, it is traversed.

### Graph definition

```genesis
graph fintech_sdlc extends standard {
  edge design → compliance_review {
    evaluators: [sox_controls_present, data_classification_complete]
    human_required: true
    convergence: human_approves
  }
  // inject compliance_review before code in the standard sequence
  sequence: [...requirements, feature_decomp, design, compliance_review,
              code ↔ unit_tests, uat_tests, cicd]
}
```

### Graph algebra

Profiles become first-class algebraic expressions over graph definitions:

```genesis
profile hotfix  = fintech_sdlc \ [feature_decomp, compliance_review]
profile audit   = fintech_sdlc + [audit_trail_edge]
profile minimal = fintech_sdlc ∩ [code ↔ unit_tests]
```

The three operators are:
- `\` — graph subtraction (remove edges from the base topology)
- `+` — graph addition (add edges to the base topology)
- `∩` — graph intersection (keep only the named edges)

This replaces profile `skip` lists with genuine set algebra. The result is checkable: a profile is always a valid subgraph of its base topology or an extension of it — never an arbitrary ad hoc collection.

### Operator definitions

Functional units (F_D, F_P, F_H) are declared in the GTL and bound to implementations:

```genesis
operator pytest          : F_D  bind "python -m pytest {test_path} -v"
operator coverage        : F_D  bind "python -m pytest --cov={src_path} --cov-fail-under={threshold}"
operator llm_gap_analysis: F_P  bind mcp::claude-code-runner
operator human_approval  : F_H  bind interactive
```

Operators declared in the GTL are the evaluator registry. The engine resolves evaluator names in edge definitions by looking them up in this registry — no hardcoding in Python.

### Higher-order compositions

Named compositions (ADR-S-026) become first-class GTL constructs:

```genesis
composition tdd_cycle(feature, code_asset, test_asset) {
  iterate(code_asset ↔ test_asset)
  until all_tests_pass and coverage >= 80
  timeout 2h
  on_stuck: escalate(human_approval)
}

composition review_gate(feature, asset) {
  human_approval(asset)
  until approved or dismissed
  on_dismiss: fold_back(parent: feature)
}
```

These are callable from edge definitions and can be composed:

```genesis
edge code ↔ unit_tests {
  execute: tdd_cycle(feature, "src/", "tests/")
  on_convergence: review_gate(feature, "src/")
}
```

### Resource location

Resource paths are currently hardcoded in the Python engine. GTL makes them projections:

```genesis
workspace {
  events   at ".ai-workspace/events/"
  features at ".ai-workspace/features/"
  spec     at "specification/"
  impl     at "imp_${tenant}/" | "src/"   // try tenant dir, fall back to src/
  tests    at "${impl}/tests/"
}
```

The `${tenant}` variable is resolved from `project_constraints.yml`. This makes multi-tenant layouts genuinely flexible rather than a naming convention enforced by the engine.

---

## Consequences

### What changes

**Static files become derived artifacts.**
`graph_topology.yml`, `edge_params/*.yml`, and `profiles/*.yml` are generated by the GTL compiler from `genesis.gen`. They remain readable for human inspection and for tools that consume them (genesis_monitor, the Python engine), but they are no longer the source of truth.

**The marketplace ships GTL programs, not file bundles.**
A methodology vendor publishes a `genesis.gen` file (and optionally operator bindings). Installing a methodology means instantiating a GTL program with project-specific values, not unpacking a file bundle. This is the design marketplace (plugin.json `description` field, v3.0.1) made concrete.

**Profiles become checkable.**
Graph algebra produces profiles whose validity is formally checkable: a profile must be a valid subgraph (or extension) of its base topology. The current skip-list approach has no such guarantee.

**The LLM reasons over GTL, not YAML.**
The LLM loaded with the bootloader currently reads YAML configs as context. A GTL program is denser, more expressive, and more directly connected to the formal system (four primitives, graph algebra, operator registry). The LLM can reason over the graph definition itself rather than inferring structure from flat key-value pairs.

### What does not change

- The event log (`.ai-workspace/events/events.jsonl`) — unchanged; source of truth
- Feature vectors (`.yml`) — unchanged; projections of the event stream
- `project_constraints.yml` — unchanged; the values layer
- The engine's `invoke()` contract (ADR-S-016) — unchanged; GTL compiles to the same invocation surface
- The iterate function — unchanged; `iterate(Asset, Context[], Evaluators)` is still the only operation

### What is deferred

- GTL parser and compiler implementation — this ADR establishes the language design; implementation is a separate feature vector
- Backward compatibility with existing YAML-only installations — GTL adoption is opt-in; the YAML surface remains valid until GTL is proven
- IDE tooling (syntax highlighting, schema validation, LSP) — deferred to post-v1.0 GTL

---

## The Helm Analogy — Precise Mapping

| Helm concept | Genesis GTL equivalent |
|-------------|----------------------|
| Chart (`templates/`) | `genesis.gen` — GTL methodology program |
| `values.yaml` | `project_constraints.yml` |
| Chart release | Converged workspace state (events + vectors) |
| `helm install -f values.yaml` | `genesis apply genesis.gen --project constraints.yml` |
| Subchart composition | Spawn/fold-back graph composition in GTL |
| Chart repository / Artifact Hub | Genesis design marketplace |
| Helm hooks | GTL operator lifecycle bindings |
| `helm upgrade` | GTL re-application when methodology version changes |

**Where Helm diverges**: Helm renders templates to static manifests and hands off to Kubernetes. GTL produces a live topology that the engine traverses during iteration — the graph stays active, not compiled away. This is closer to a query language (the graph is the program) than a template language (the graph compiles to data).

---

## Relationship to Prior ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-S-016 (Invocation Contract) | GTL compiles to the same `invoke(intent, state) → StepResult` surface. Unchanged. |
| ADR-S-026 (Named Compositions) | GTL makes named compositions first-class syntax instead of YAML-encoded strings. Supersedes the YAML encoding; the semantics are unchanged. |
| ADR-S-029 (Dispatch Contract) | GTL operator bindings define the dispatch registry. EDGE_RUNNER resolves operators from the GTL registry rather than hardcoded config. |
| ADR-S-032 (IntentObserver/EDGE_RUNNER) | EDGE_RUNNER's graph traversal reads the live GTL topology rather than `graph_topology.yml`. The dispatch contract is unchanged. |
| ADR-S-033 (Genesis-Enabled Systems) | Genesis-enabled systems can publish their own GTL graphs describing their REQ key topology. This makes the bridge contract (spec→code→telemetry→intent) expressible in GTL. |
| ADR-S-034 (Genesis Ecosystem) | Ecosystem niche discovery becomes GTL graph composition: a service publishes its REQ key graph; dependents compose it as a subchart. |

---

## Open Questions

1. **Syntax**: GTL syntax above is illustrative. Should it be a custom syntax (new parser), a Python internal DSL (fluent API), or a superset of YAML (YAML + includes + expressions)? Each has different LLM-readability trade-offs.

2. **Compilation target**: Does GTL compile to the current YAML files (backward compat), or does the engine consume GTL directly (cleaner, breaks existing installations)?

3. **Versioning**: A GTL methodology program has a version. When it changes, what happens to in-progress workspace state? (Helm has `helm upgrade` semantics — apply the diff.)

4. **Operator registry scope**: Are operators global (one registry per installation) or scoped to a graph definition? Global is simpler; scoped enables operator overloading per methodology.

5. **GTL as spec**: Should the Genesis specification itself be expressed in GTL? (The SDLC graph in §XIV of the bootloader is already written as a graph — GTL would make it executable.)

---

## Status

PROPOSAL — not yet ratified. Pending:
- Cross-tenant review (Claude, Codex, Gemini implementations)
- Spike vector to validate GTL grammar expressiveness against current YAML surface
- Resolution of Open Question 1 (syntax choice) before implementation begins

*Raised from steering conversation, 2026-03-11.*
