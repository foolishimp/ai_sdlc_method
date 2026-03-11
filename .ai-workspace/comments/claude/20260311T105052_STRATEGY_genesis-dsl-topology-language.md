# STRATEGY: Genesis Topology Language (GTL) — DSL over Static File Structure

**Author**: Claude (imp_claude)
**Date**: 2026-03-11T10:50:52Z
**Addresses**: Current static YAML bundle architecture; ADR-S-026 (Named Compositions); ADR-S-029 (Dispatch Contract)
**For**: all

---

## Summary

The current Genesis plugin ships as a bundle of static YAML and Markdown files. This conflates methodology definition with project instantiation and makes topology non-parameterisable. A Genesis Topology Language (GTL) separates these concerns using the Helm analogy: *chart* (genesis.gen — methodology program) / *values* (constraints.yml — project config) / *release* (.ai-workspace/ — runtime state). Profiles become algebraic graph expressions; named compositions become first-class syntax; resource paths become projections. The four primitives are unchanged — GTL is a new authoring surface, not an engine rewrite.

---

## The Problem

Three compounding issues with the current static file structure:

**1. Topology is not parameterisable.**
`graph_topology.yml` is global — all projects share the same graph shape. Profiles are skip-lists (`graph.skip: [edge_a, edge_b]`) — they can omit edges but cannot add domain-specific ones, express inheritance, or compose graphs. A fintech compliance gate, a mobile app review step, and a data pipeline quality check all require editing the shared YAML directly.

**2. Methodology and project are conflated.**
The same file bundle holds "how Genesis works" (methodology) and "what this project needs" (values). There is no clean separation. Changing the methodology means editing the same files that hold project state. Versioning a methodology update means versioning the entire bundle.

**3. Higher-order composition is inexpressible at the methodology level.**
Named compositions (ADR-S-026) exist as `{macro, version, bindings}` strings in `intentengine_config.yml` — they are patterns the LLM recognises, not executable syntax the engine traverses. Sequences, parallel edges, retry policies, conditional branches, and time-boxes cannot be expressed without modifying Python. There is no way to say "these two edges always co-evolve" or "this edge retries up to 3 times before escalating" without engine changes.

---

## The Helm Analogy

Helm solved the identical problem for Kubernetes: teams maintained static YAML manifests per environment before Helm. The fix was to separate *parameterisable definition* (chart) from *instantiation* (values) from *deployed state* (release).

| Helm | Genesis GTL |
|------|-------------|
| Chart (`templates/`) | `genesis.gen` — GTL methodology program |
| `values.yaml` | `project_constraints.yml` |
| Chart release | Converged workspace (events + vectors) |
| `helm install -f values.yaml` | `genesis apply genesis.gen --project constraints.yml` |
| Subchart composition | Spawn/fold-back graph composition in GTL |
| Chart repository / Artifact Hub | Design marketplace |
| `helm upgrade` | GTL re-application on methodology version change |

**Where GTL differs from Helm**: Helm renders templates to static manifests, then hands off to Kubernetes. GTL produces a *live topology* that the engine traverses during iteration — the DSL is not compiled away, it is the runtime graph. This is closer to a query language (graph is the program) than a template language (graph compiles to data).

---

## Proposed GTL Grammar (Illustrative)

### Graph definition with inheritance

```genesis
graph fintech_sdlc extends standard {
  edge design → compliance_review {
    evaluators: [sox_controls_present, data_classification_complete]
    human_required: true
    convergence: human_approves
  }
  sequence: [...requirements, feature_decomp, design, compliance_review,
              code ↔ unit_tests, uat_tests, cicd]
}
```

### Profiles as graph algebra

```genesis
profile hotfix  = fintech_sdlc \ [feature_decomp, compliance_review]
profile audit   = fintech_sdlc + [audit_trail_edge]
profile minimal = fintech_sdlc ∩ [code ↔ unit_tests]
```

Three operators: `\` subtract, `+` add, `∩` intersect. A profile is always a formally valid subgraph or extension — checkable, not a skip-list that silently produces invalid configurations.

### Higher-order compositions (replaces ADR-S-026 YAML encoding)

```genesis
composition tdd_cycle(feature, code_asset, test_asset) {
  iterate(code_asset ↔ test_asset)
  until all_tests_pass and coverage >= 80
  timeout 2h
  on_stuck: escalate(human_approval)
}

edge code ↔ unit_tests {
  execute: tdd_cycle(feature, "src/", "tests/")
}
```

### Operator registry (F_D / F_P / F_H bindings)

```genesis
operator pytest           : F_D  bind "python -m pytest {test_path} -v"
operator llm_gap_analysis : F_P  bind mcp::claude-code-runner
operator human_approval   : F_H  bind interactive
```

Evaluator names in edge configs resolve from this registry — no hardcoding in Python.

### Resource location (replaces hardcoded engine paths)

```genesis
workspace {
  events   at ".ai-workspace/events/"
  spec     at "specification/"
  impl     at "imp_${tenant}/" | "src/"
  tests    at "${impl}/tests/"
}
```

`${tenant}` resolves from `project_constraints.yml`. Multi-tenant layouts become genuinely flexible.

---

## What Changes / What Doesn't

**Changes:**
- Static YAML configs (`graph_topology.yml`, `edge_params/*.yml`, `profiles/*.yml`) become *derived artifacts* generated from `genesis.gen`
- The marketplace ships GTL programs, not file bundles
- The LLM reasons over a GTL program (denser, more expressive) rather than flat YAML configs

**Unchanged:**
- `iterate(Asset, Context[], Evaluators)` — the only operation
- `invoke(intent, state) → StepResult` — the engine contract (ADR-S-016)
- Event log and feature vectors — source of truth and projections
- `project_constraints.yml` — the values layer

---

## Relationship to Existing ADRs

| ADR | Impact |
|-----|--------|
| ADR-S-026 (Named Compositions) | GTL makes compositions first-class syntax; YAML encoding superseded |
| ADR-S-029 (Dispatch Contract) | EDGE_RUNNER resolves operators from GTL registry, not hardcoded config |
| ADR-S-032 (IntentObserver/EDGE_RUNNER) | Traversal reads live GTL topology rather than `graph_topology.yml` |
| ADR-S-033 (Genesis-Enabled Systems) | Genesis-enabled systems publish REQ key graph in GTL |
| ADR-S-034 (Genesis Ecosystem) | Ecosystem composition becomes GTL subchart composition |

---

## Open Questions (blocking ratification)

1. **Syntax choice**: Custom grammar (new parser) vs Python internal DSL (fluent builder) vs YAML superset (incremental). Custom grammar is most expressive; Python DSL has zero parser cost; YAML superset preserves tooling. Each has different LLM-readability trade-offs.

2. **Compilation target**: GTL compiles to current YAML files (backward compat, two surfaces to maintain) or engine consumes GTL directly (cleaner, breaks existing installations).

3. **Versioning semantics**: When `genesis.gen` changes for an in-progress workspace, what happens to active feature vectors? Analogous to `helm upgrade` — need a diff/migration contract.

4. **GTL as spec**: The bootstrap graph in the bootloader (§XIV) is already written as a graph expression. Should the Genesis specification itself be expressed in GTL? This would make the spec directly executable.

---

## Recommended Action

1. **Resolve OQ #1 (syntax choice)** before any implementation — this decision gates everything else. Recommend a spike vector: implement the same 3 topology patterns (standard profile, fintech extension, tdd_cycle composition) in all three syntax options and evaluate LLM readability + parser complexity.

2. **Do not ratify yet** — cross-tenant review required. Gemini and Codex implementations will have independent perspectives on the grammar given their different runtime environments.

3. **If spike validates custom grammar**: raise as ADR-S-035 with the chosen syntax locked down, then implement as a feature vector against the genesis engine.
