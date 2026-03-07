# ADR-028: Genesis Monitor as Trajectory Visualisation Tool

**Status**: Accepted
**Date**: 2026-03-07
**Deciders**: Methodology Author
**Requirements**: REQ-TOOL-002 (Status Command), REQ-SUPV-001 (Self-Observation)
**Extends**: ADR-022 (Instance Graph from Events), ADR-011 (Consciousness Loop)
**Spec References**: ADR-S-020 (Phase Space and Hamiltonian), ADR-S-019 (Markov Blankets)

---

## Context

ADR-022 defined the instance graph: a projection of `events.jsonl` into the current position of each feature in the graph. The blocked item in ACTIVE_TASKS.md "Add zoom level 1 overlay to `graph.py` — BLOCKED (genesis_monitor not in imp_claude)" reflected that the visualisation layer was missing.

The genesis monitor exists as a separate FastAPI project at `ai_sdlc_examples/local_projects/genisis_monitor`. It reads `events.jsonl` from a monitored project workspace and provides real-time projections:
- `projections/convergence.py` — EdgeConvergence table from events
- `projections/temporal.py` — feature trajectory reconstruction with time scrubbing
- `projections/graph.py` — graph topology view
- `models/core.py` — data models (EdgeConvergence, FeatureVector, EdgeTrajectory)

The monitor is already capable of reading the methodology's events. The gap was:
1. No Hamiltonian (H = T + V) computed anywhere in the projection pipeline
2. No formal decision capturing the genesis monitor as the canonical visualisation tool
3. No connection between the (graph × time) trajectory model (ADR-S-020) and the monitor's implementation

---

## Decision

### 1. Genesis Monitor is the Canonical Visualisation Tool for Trajectory Data

The genesis monitor (`ai_sdlc_examples/local_projects/genisis_monitor`) is designated as the **canonical external visualisation tool** for the methodology's (graph × time) trajectory data.

It is **external** to `imp_claude/` — consistent with the multi-tenancy model (ADR-S-002). The monitor is not methodology code; it is an observer of the event stream, reading `events.jsonl` as the sole integration contract.

### 2. The Event Stream is the Integration Contract — The Monitor Reads Only

The genesis monitor must not write to the monitored project's workspace. It reads:
- `.ai-workspace/events/events.jsonl` — the primary data source (time axis)
- `.ai-workspace/graph/graph_topology.yml` — graph structure
- `.ai-workspace/features/active/*.yml` — current feature vector state (supplementary)

All projections are derived. The monitor is a pure observer — consistent with the Markov blanket model (ADR-S-019): the sensory system observes without perturbing internal states.

### 3. Hamiltonian H = T + V Added to EdgeConvergence

The `EdgeConvergence` model (`models/core.py`) gains:
```python
hamiltonian: int = 0  # H = T + V (iterations + last_delta) — iteration cost
```

Computed in `projections/convergence.py` `build_convergence_table_from_events()`:
```python
T = state["iterations"]
V = state["delta_curve"][-1] if state["delta_curve"] else 0
hamiltonian = T + V
```

This provides the canonical cost metric at every edge in the convergence table.

### 4. The Monitor Resolves the ADR-022 Blocked Item

ADR-022 Step 5 "Add zoom level 1 overlay to `graph.py` — BLOCKED (genesis_monitor not in imp_claude)" is resolved:
- The genesis monitor IS the graph.py zoom level — it is a separate process, not code inside imp_claude
- The methodology's `gen-status` command does not need to replicate the monitor — it provides the text-based status view; the monitor provides the visual trajectory view
- The integration point is `events.jsonl` — the monitor watches it via filesystem events and updates in real time

### 5. The Monitor Watches the This Repo's Workspace During Development

For dogfooding: the genesis monitor can be pointed at `ai_sdlc_method/.ai-workspace/events/events.jsonl` to observe the methodology developing itself. This closes the self-observation loop (§XV bootloader — the methodology tooling is itself a product and must monitor itself).

---

## Consequences

### Positive

- ADR-022 blocked item resolved without adding monitor code to `imp_claude/`
- Hamiltonian H is now computed in the genesis monitor and visible in the convergence table
- Clear integration contract: events.jsonl is the sole coupling point
- Self-observation during development: monitor can watch the methodology's own event stream

### Negative

- The genesis monitor is a separate process — not automatically started when the methodology is used. Developers must start it manually. This is acceptable: it is an optional visualisation layer, not required for methodology operation.
- The monitor location (`ai_sdlc_examples/`) is outside the main repo. This is a known trade-off — the monitor is a separate project being developed under the genesis methodology itself (dogfooding).

### Neutral

- `gen-status --gantt` (text Gantt in STATUS.md) and the genesis monitor Gantt projection are parallel projections — same data, different rendering. Both are valid; they serve different contexts (CLI vs. web UI).

---

## References

- ADR-022: Instance Graph from Events (blocked item resolved)
- ADR-S-019: Markov Blankets — sensory system reads without perturbing internal states
- ADR-S-020: Phase Space and Hamiltonian — the projection the monitor implements
- Genesis Monitor location: `ai_sdlc_examples/local_projects/genisis_monitor`
  - Stack: Python FastAPI + SSE + HTML/CSS templates
  - Key modules: `projections/convergence.py`, `projections/temporal.py`, `models/core.py`
  - `EdgeConvergence.hamiltonian` — H added 2026-03-07
