# ADR-S-007: Module Decomposition and Basis Projections as Graph Nodes

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Scope**: Build architecture — `core/AI_SDLC_ASSET_GRAPH_MODEL.md`, `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`

---

## Context

The bootstrap graph previously moved from Design directly to Code:

```
... → Design → Code ↔ Tests → ...
```

While Feature Decomposition (ADR-S-006) structured the *product* into buildable units, it did not structure the *codebase* itself. Architecture (Design) was being implemented as a flat file structure or a single module, leading to:

1. **Monolithic implementation drift.** Without a formal step to map architectural components to code modules, agents default to the simplest possible file structure.
2. **Untraceable build architecture.** Decisions about module boundaries, dependency cycles between packages, and build-system configuration were implicit and unvalidated.
3. **Sequential bottlenecking.** Parallel construction requires orthogonal code modules. Without a formal decomposition, multiple agents work in the same files, creating merge conflicts and dependency tangles.
4. **The "Basis Projection" gap.** A feature (from Feature Decomposition) often spans multiple modules. There was no formal way to project a feature onto the specific modules it touches before coding began.

---

## Decision

### Add Module Decomposition and Basis Projections nodes

The graph between Design and Code becomes:

```
Design → Module Decomposition → Basis Projections → Code
```

### What Module Decomposition produces

| Output | Description |
|--------|-------------|
| **Module Map** | Mapping of architectural components to code packages/modules |
| **Dependency DAG** | The internal code-level dependency graph (must match design constraints) |
| **Interface Contracts** | Public APIs between modules (F_D-verifiable) |
| **Build Config** | `build.sbt`, `setup.py`, `package.json` scaffolding |

### What Basis Projections produce

A **Basis Projection** is the intersection of a Feature (from Feature Decomposition) and a Module (from Module Decomposition).

| Output | Description |
|--------|-------------|
| **Projected Intent** | The specific part of Feature F that must be implemented in Module M |
| **Local Interface** | The part of the module interface required by this feature |
| **Stub/Mock Specs** | What other modules this projection assumes exist |

#### Basis Projection artifact format

Each projection is a short structured document:

```
Projection: REQ-F-AUTH-001 × auth-module
─────────────────────────────────────────
Feature:     REQ-F-AUTH-001 — User Authentication
Module:      auth-module

Scope in this module:
  - Validate credentials against the user store
  - Issue a session token on success
  - Emit auth_attempted event (success or failure)

Out of scope for this module:
  - User registration (user-module)
  - Session expiry enforcement (session-module)

Required interface from other modules:
  - user-module: lookup_user(id) → User | NotFound
  - session-module: create_session(user_id) → Token

Exposed interface (for other modules to depend on):
  - authenticate(credentials) → Token | AuthError

Evaluator contract:
  - authenticate() returns Token on valid credentials
  - authenticate() returns AuthError (not exception) on invalid credentials
  - auth_attempted event emitted on every call
```

One such document per (feature × module) intersection in the MVP scope. An implementer working on `auth-module` sees exactly what they need to build and what they can stub — with no knowledge of other features' internals required.

### Markov Criteria

**Module Decomposition** is stable when:
- Every component in the Design is mapped to at least one module.
- The module dependency DAG is acyclic and matches architectural constraints.
- Interface contracts are defined for all inter-module calls.

**Basis Projections** are stable when:
- Every feature in the MVP scope is projected onto its required modules.
- The sum of all projections for Feature F equals the intent of Feature F.
- All projections for a module are consistent with the module interface.

---

## Consequences

**Positive:**
- **Orthogonal Parallelism**: Agents can work on different basis projections simultaneously with zero coordination cost, as they are bounded by the module interfaces.
- **Traceable Build**: Build-system structure is a first-class asset with its own evaluators.
- **Improved Design Fidelity**: The mapping from architecture to code is explicit and validated.

**Negative / Trade-offs:**
- Adds two mandatory nodes for complex projects.
- Small projects (PoC) will collapse these nodes via the `poc` projection profile.

---

## Alternatives Considered

**Collapse into Design**: Keep Design responsible for both architecture and module mapping. Rejected — design operates at the component/interface level; module structure is a separate concern that requires its own convergence criteria. Conflating them produces designs that are either too coarse (no module boundary) or too detailed (implementation in a design doc).

**Single Module Decomposition node (no Basis Projections)**: Add module mapping without the projection step. Considered. Sufficient for single-agent sequential builds. Rejected for the standard profile because it forfeits parallel construction — without explicit basis projections, agents cannot work on isolated scopes bounded by module interfaces.

**Keep as zoom intermediates (§2.5)**: Leave Module Decomposition and Basis Projections as implicit nodes that only appear when the Design → Code edge is zoomed in. What we had. Rejected for the same reason Feature Decomposition was promoted (ADR-S-006): implicit steps have no evaluator checklist and no convergence criterion. Without a formal node, the module structure is undocumented and unvalidated.

**PoC collapse**: For profiles where build architecture is trivial (single-file scripts, PoC experiments), these nodes remain collapsible via projection profiles. This is the `poc` and `spike` zoom behavior — not an alternative for the standard path.

---

## References

- [core/AI_SDLC_ASSET_GRAPH_MODEL.md](../core/AI_SDLC_ASSET_GRAPH_MODEL.md) §2.5, §6.7
- [ADR-S-006](ADR-S-006-feature-decomposition-node.md) — upstream dependency; same rationale applied to Design→Code intermediates
