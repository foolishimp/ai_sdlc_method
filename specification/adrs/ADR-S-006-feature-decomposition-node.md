# ADR-S-006: Feature Decomposition as an Explicit Graph Node

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Scope**: Bootstrap graph topology — `core/AI_SDLC_ASSET_GRAPH_MODEL.md`, `graph_topology.yml`

---

## Context

The bootstrap graph previously had a direct edge from Requirements to Design:

```
Intent → Requirements → Design → Code ↔ Tests → ...
```

In practice, before any architecture decision was made, practitioners were producing a feature decomposition document — a list of buildable units, their dependency graph, and their build order. The `specification/features/FEATURE_VECTORS.md` document even stated: *"This is the prerequisite for design — per the methodology, features are identified before architecture is drawn."*

Yet this step had no formal node in the graph. Consequences:

1. **Implicit, inconsistent execution.** Some practitioners decomposed features thoroughly; others went straight to architecture. Without a formal node, there was no evaluator checklist, no convergence criterion, and no human approval gate for the feature plan.

2. **Architecture decisions driven by random assumptions.** A design that starts from "74 requirements" tends to produce a monolith or a structure that mirrors the req numbering. A design that starts from "11 features in this dependency order, with this MVP boundary" produces architecture that mirrors the domain. The feature decomposition is the design input, not the full requirements list.

3. **MVP scoping happened at design time.** Practitioners first drew the architecture, then tried to cut scope. This produces an architecture that isn't actually right for the MVP — it was designed for the full system and then cut. MVP scoping belongs before architecture, at the feature dependency level.

4. **Tech choices crept into feature planning.** Without a formal tech-agnosticism check on the feature plan, it was easy to produce features like "PostgreSQL user table feature" rather than "user management feature." The feature decomposition is spec, not design.

5. **The spec/design boundary was at the wrong place.** The formal statement said the boundary was at `Requirements → Design`. In reality, Feature Decomposition is as tech-agnostic as Requirements — it describes WHAT to build (and in what order), not HOW to build it.

---

## Decision

### Add Feature Decomposition as an explicit node

The bootstrap graph becomes:

```
Intent → Requirements → Feature Decomposition → Design → Code ↔ Tests → UAT → CI/CD → Telemetry → Intent
```

The `Requirements → Design` edge is removed from the standard graph. The two new edges are:
- `Requirements → Feature Decomposition`
- `Feature Decomposition → Design`

### What Feature Decomposition produces

| Output | Description |
|--------|-------------|
| **Feature list** | Every REQ-F-* key grouped into named, user-facing features |
| **Dependency DAG** | Which features must converge before others can start |
| **Build order** | Topological sort of the DAG |
| **MVP scope** | The minimum connected subgraph that delivers real value |
| **REQ key coverage** | Each REQ-F-* key assigned to exactly one feature |

### The spec/design boundary moves

The boundary is now at **Feature Decomposition → Design**, not `Requirements → Design`.

Feature Decomposition is on the spec side: it describes WHAT to build and in what order, in purely functional terms. It is tech-agnostic — valid across all implementations.

Design begins at the Feature Decomposition → Design edge, where technology binding occurs.

### Tech-agnosticism is an evaluator criterion

The `requirements_feature_decomp.yml` edge params include a hard evaluator:

> The feature decomposition contains no technology references. Features describe WHAT (user capability), not HOW (implementation).

Any feature description that names a technology, framework, database, or cloud provider fails this check.

### Profile zoom behavior

| Profile | Behavior |
|---------|---------|
| `full`, `standard` | Feature Decomposition is an explicit mandatory waypoint |
| `poc` | Feature Decomposition node collapsed: `Requirements → Design` directly |
| `spike` | Both Requirements and Feature Decomposition collapsed |

This is a zoom operation (§2.5 of the formal system): the intermediate becomes explicit at higher fidelity, collapsed at lower.

### Markov criteria for feature_decomposition

An asset achieves Markov object status when:
1. All REQ-F-* keys are assigned to exactly one feature (no orphans, no duplicates)
2. The dependency DAG is acyclic (topological sort succeeds)
3. Build order is derivable from the DAG
4. MVP scope is explicitly marked (human decision, not derived)
5. Human approves the feature plan

---

## Consequences

**Positive:**
- Architecture decisions are made against a structured, dependency-ordered feature plan, not raw requirements. This reliably produces better-structured design.
- MVP scoping is a formal spec operation (select connected subgraph) that happens before architecture — not a retrospective cut after design.
- Tech-agnosticism of the feature plan is a hard evaluator check: it cannot silently drift toward implementation detail.
- The spec/design boundary is correctly stated: Feature Decomposition is spec; Design begins technology binding.
- `FEATURE_VECTORS.md` is now the canonical artifact for this node — its existing content structure (feature list with dependencies) matches the Markov criteria exactly.

**Negative / trade-offs:**
- One additional node in the standard graph means one additional iteration cycle before design. For large requirement sets, this is net positive; for small PoC work, this is collapsible via zoom.
- The `Requirements → Design` direct edge is removed from the standard graph. Existing implementations that skip Feature Decomposition must update their graph topology or use a profile that collapses the node.
- Edge params for `Feature Decomposition → Design` reuse much of `requirements_design.yml` but now receive a structured feature plan as source rather than raw requirements. The design agent guidance must be updated to read the feature plan.

---

## Alternatives Considered

**Keep Feature Decomposition as an informal pre-step**: What we had. Rejected — informal steps without evaluators produce inconsistent output. The whole value of the formal system is that every step has a convergence criterion.

**Merge Feature Decomposition into Requirements**: Make the requirements document itself carry the feature groupings and dependency DAG. Rejected — this conflates two distinct things: what the system must do (requirements) and how that decomposes into buildable units (features). The requirements are the authoritative spec; the feature decomposition is derived from them and can be revised without changing the requirements themselves.

**Put Feature Decomposition on the design side**: Make it tech-bound. Rejected — the feature dependency graph is purely logical (domain dependency), not technical (module dependency). The same feature plan is valid for a microservices architecture, a monolith, or a serverless design. Binding it to a technology choice forfeits the "one spec, many designs" property.

---

## References

- [core/AI_SDLC_ASSET_GRAPH_MODEL.md](../core/AI_SDLC_ASSET_GRAPH_MODEL.md) §2.1 — updated bootstrap graph
- [features/FEATURE_VECTORS.md](../features/FEATURE_VECTORS.md) — canonical Feature Decomposition artifact for this methodology
- [ADR-S-004](ADR-S-004-derivation-constraint.md) — Feature Decomposition derives from Requirements; downstream may not contradict upstream
- [ADR-S-002](ADR-S-002-multi-tenancy-model.md) — Feature Decomposition is shared spec; implementations read it, do not own it
- `imp_claude/code/.claude-plugin/plugins/genesis/config/edge_params/requirements_feature_decomp.yml` — evaluator checklist for this edge
