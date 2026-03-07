# ADR-S-020: Feature Trajectories as Phase Space Paths and the Hamiltonian Cost Metric

**Status**: Accepted
**Date**: 2026-03-07
**Deciders**: Methodology Author
**Requirements**: REQ-TOOL-002 (Status Command), REQ-SUPV-001 (Self-Observation), REQ-LIFE-009 (Spec Review as Gradient Check)
**Extends**: ADR-S-019 (Markov Blankets and Active Inference), ADR-S-012 (Event Stream as Formal Model Medium)
**Supersedes**: Nothing — extends the feature vector model (§6) with trajectory and cost semantics

---

## Context

### Feature Vectors as Positions vs. Trajectories

The Asset Graph Model defines a feature vector as a trajectory through the graph (§6.1):

```
Feature F = |req⟩ + |design⟩ + |code⟩ + |unit_tests⟩ + ...
```

But the existing treatment models features as **positions** — which edge are they currently at? This loses the historical dimension: how many iterations were spent to reach that position, what was the cost of convergence at each edge, and how fast or slow was the convergence rate?

Features are not positions. They are **trajectories in (graph × time) space** — paths through a phase space that has both a spatial dimension (which edge) and a temporal dimension (the event log).

### Phase Space and the Hamiltonian

In classical mechanics, a Hamiltonian system is characterised by:
- A **configuration space** q (position)
- A **momentum space** p (rate of change)
- A **Hamiltonian** H(q, p) = T + V (total energy = kinetic + potential)

The Constraint-Emergence Ontology (§VI multi-domain mapping table, CEO) notes that the Hamiltonian is a **manifold-level description** of constraint propagation — it describes the cost of traversal at the projection level, not the underlying constraint topology. This is important: the Hamiltonian is observable from the event log without knowing the underlying constraint structure.

In the methodology's domain:
- q = edge index in the graph (position in the SDLC traversal)
- p = convergence rate = −d(delta)/d(iteration) (how fast the gradient is being reduced)
- T = total iterations completed to date (kinetic energy — work already done)
- V = current delta (failing evaluators) (potential energy — work remaining)
- **H = T + V** (the Hamiltonian — total iteration cost at any point in the traversal)

The Hamiltonian is the **cost metric** of the traversal. It is fully computable from `events.jsonl`:

```
For each (feature, edge, iteration_k):
  T_k = cumulative iterations across all preceding edges + iteration_k
  V_k = delta at iteration_k (failing check count from evaluators)
  H_k = T_k + V_k
```

### Time as a Dimension — events.jsonl as the Time Axis

The Constraint-Emergence Ontology defines time as an **emergent measure of change on a constraint surface** — not a fundamental dimension, but a derived measure of discrete steps in the constraint network's evolution. In the methodology:

- Each `iteration_completed` event is one unit of change on the constraint surface
- The event sequence in `events.jsonl` IS the time dimension — ordered by actual occurrence, not by clock time
- The "point map" of all in-flight features at any moment is a cross-section of this (graph × time) space at a given event index

This means:
- Features that converge quickly are traversing a **sparse constraint surface** — few conflicts, evaluators agree
- Features that take many iterations are traversing a **dense constraint surface** — many conflicts, evaluators surface additional requirements
- The convergence rate `−dH/dt` is a direct observable of constraint surface density
- The genesis monitor reads this data from `events.jsonl` — the event log IS the time dimension

### The Genesis Monitor

The genesis monitor (a separate FastAPI application at `ai_sdlc_examples/local_projects/genisis_monitor`) already projects `events.jsonl` into convergence tables and temporal reconstructions. It has:
- `delta_curve: list[int]` per edge — the history of V over iterations
- `iterations: int` per edge — the T component

The Hamiltonian is the natural derived metric that the monitor should expose: H = T + V at each point, making the cost of traversal visible as a scalar alongside the delta curve.

---

## Decision

### 1. Features are Trajectories in Phase Space — Not Positions

The specification (§6.8) formally adopts the phase space model:

```
Phase space: (q, p) where
  q = edge index (position in the graph)
  p = convergence rate = −d(delta)/d(iteration)

A feature's complete trajectory = the sequence of (q_k, p_k, H_k) over all events
```

The "point map" view — showing all in-flight features at their current (edge, iteration) coordinates — is a cross-section of this phase space at the current moment in the event log.

The Gantt chart (§7.4.2) is a further projection: it projects the (graph × time) space onto a calendar timeline. The phase space representation is more fundamental — calendar time is a derived view.

### The Hamiltonian H = T + V is the Canonical Iteration Cost Metric

The Hamiltonian is adopted as the **canonical cost metric** for feature traversal:

| Symbol | Definition | Observable from |
|--------|-----------|----------------|
| T | Total iterations completed to date | `iteration` field in events, accumulated |
| V | Current delta (failing evaluator count) | `delta` field or evaluator results in events |
| H = T + V | Total Traversal Cost (Sunk + Remaining) | Derived from T and V at any point |

**H diagnostic patterns (assuming dt = 1 iteration):**

| Pattern | Interpretation | Logic |
|---------|---------------|-------|
| **dH/dt < 0** | Super-linear convergence | Resolving > 1 check per iteration |
| **dH/dt = 0** | Unit-efficient convergence | Resolving exactly 1 check per iteration (Healthy) |
| **dH/dt > 0** | High-friction / Dense surface | Resolving < 1 check per iteration (Inefficient) |
| **dH/dt = 1** | Blocked feature | dV/dt = 0. Effort (T) spent with zero progress (V) |

H is computed from the event log — it does not require any additional instrumentation.

### 3. events.jsonl is the Time Axis — Time is Iteration Count, Not Clock Time

For the purpose of phase space analysis, the **time axis** is the iteration sequence in `events.jsonl`, not wall clock time. This is consistent with the CEO definition: time = emergent measure of change on a constraint surface.

Consequence: two features that take the same number of iterations but different calendar durations have the **same trajectory shape** in iteration space. Calendar duration is a separate projection — relevant for scheduling and Gantt, not for convergence analysis.

The genesis monitor supports both projections:
- **Iteration space**: convergence table, delta curve, Hamiltonian per edge — iteration count as x-axis
- **Calendar space**: Gantt chart, temporal reconstruction — wall clock time as x-axis

### 4. The Genesis Monitor Computes H as a Standard Projection

The genesis monitor is designated as the **canonical visualisation tool** for (graph × time) trajectory data. It must:

1. Compute `hamiltonian: int = iterations + last_delta` on every `EdgeConvergence` projection
2. Expose H in the convergence table alongside `iterations` and `delta_curve`
3. Support a "point map" view: all active features plotted at their current (edge_index, H) coordinates
4. Colour or size features by H — high H = high remaining cost or high sunk cost

Implementation note: `EdgeConvergence.hamiltonian` was added to `models/core.py` and computed in `projections/convergence.py` in the genesis monitor codebase.

### 5. Convergence Rate as Constraint Surface Density Observable

The delta drop rate `−dV/dt` (how fast failing evaluators resolve per iteration) is the direct observable of constraint surface density:

- **−dV/dt > 1** (super-linear convergence) → sparse constraint surface → few conflicts → well-specified requirements
- **−dV/dt = 1** (unit-efficient convergence) → normal, healthy traversal — one check resolved per iteration
- **−dV/dt = 0** (delta unchanging) → blocked → constraint surface has no admissible direction of travel from this position without a change in the constraint surface itself (spec update or evaluator relaxation)

The H diagnostic in §2 captures the same patterns via `dH/dt = 1 + dV/dt`:
- dH/dt < 0 ↔ −dV/dt > 1 (super-linear) — H drops
- dH/dt = 0 ↔ −dV/dt = 1 (healthy) — H flat
- dH/dt = 1 ↔ −dV/dt = 0 (blocked) — H rises at rate 1

H is the **cost metric** (sunk + remaining); `−dV/dt` is the **convergence signal**. Both are empirically observable from `events.jsonl` without additional instrumentation.

---

## Consequences

### Positive

- **Cost visibility**: H makes the total cost of traversal visible as a single scalar at every point in the event log — both for monitoring and for historical analysis
- **Constraint surface density**: Convergence rate becomes a direct measurement of how dense the constraint surface is at each edge — enabling evidence-based evaluation of spec quality
- **Phase space coherence**: Feature trajectories can be compared across features, across projects, and across time — they share a common phase space coordinate system
- **Genesis monitor extension**: Adding H to the convergence projection requires minimal code change (T and V were already tracked); the visualisation benefit is immediate
- **Formal grounding**: H is grounded in Hamiltonian mechanics (manifold-level description per CEO §VI) — not an invented metric

### Negative

- **Additive only**: H = T + V weights iterations and delta equally. Future refinements may want to weight by iteration cost (e.g., by LLM token cost). ADR-S-020 defers this — uniform weighting is the correct first approximation.
- **Phase space is not conserved**: Unlike classical Hamiltonian mechanics, H decreases over a healthy traversal (energy is dissipated as work). This is correct for dissipative systems — the methodology is intentionally dissipative (it converges to minima). The Hamiltonian analogy holds at the phase space structure level, not the conservation law level.

### Neutral

- The Gantt chart projection (§7.4.2, gen-status --gantt) remains valid — it is a calendar projection of the same trajectory data
- The instance graph (ADR-022) is a position map (feature at edge); the phase space view adds momentum and cost dimensions but does not replace it

---

## Relationship to Formal System

**§6.8 (Feature Vectors — Hamiltonian)**: This ADR is the decision record for §6.8.

**§7.1 (The Gradient)**: H tracks the gradient across a trajectory. The gradient at a single point is `delta(state, constraints) → work`; H accumulates that work:
```
H_total = T + V_current
```

**ADR-S-019 (Markov Blankets)**: The phase space trajectory is the trajectory of the internal state through the blanket's configuration space. H is the free energy integrated over the trajectory — the total prediction error the system has had to resolve.

---

## References

- §6.8: The Hamiltonian: Iteration Cost as Phase Space Energy
- §7.1: The Gradient — single-point delta that H accumulates
- ADR-S-019: Markov Blankets and Active Inference — free energy connection
- ADR-S-012: Event Stream as Formal Model Medium — events.jsonl as time axis
- **ADR-022 (implementation)**: Project Instance Graph — position map (H adds momentum and cost)
- Constraint-Emergence Ontology §VI: Hamiltonian as manifold-level description of constraint propagation
