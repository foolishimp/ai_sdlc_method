# ADR-GG-010: Hamiltonian Metric Display in Status Command

**Status**: Accepted
**Date**: 2026-03-07
**Author**: Gemini
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-TOOL-003, REQ-UX-003
**Extends**: ADR-S-020 (Phase Space Hamiltonian)

---

## Context

The formal specification (§6.8) adopts the **Hamiltonian ($H = T + V$)** as the canonical scalar metric for feature traversal cost. We need to define how this metric is presented to the user in the Gemini-native `aisdlc_status` tool and the `STATUS.md` artifact.

## Decision

The `StatusCommand` and its generated `STATUS.md` will explicitly display the Hamiltonian and derived diagnostic patterns.

### 1. Data Mapping

| Component | Gemini Representation | Source |
| :--- | :--- | :--- |
| **T (Work Done)** | Iteration Count | `iteration` field in `iteration_completed` events. |
| **V (Potential)** | Current Delta | `delta` field in the most recent `iteration_completed` event. |
| **H (Total Cost)** | Hamiltonian | Sum of T and V. |

### 2. UI Representation

The `STATUS.md` trajectory table will include the following columns:
- `Iteration (T)`
- `Delta (V)`
- `Hamiltonian (H)`
- `Diagnostic`

### 3. Diagnostic Classifications

| Pattern | Logic | Display Label |
| :--- | :--- | :--- |
| **$dH/dt = 0$** | Delta decreased by 1 | `Healthy` |
| **$dH/dt < 0$** | Delta decreased by > 1 | `Efficient` |
| **$dH/dt > 0$** | Delta decreased by < 1 | `Dense Surface` |
| **$dH/dt = 1$** | Delta unchanged | `Blocked` |

## Rationale

### Why This Visualization

1.  **Alignment**: Directly fulfills the spec-level requirement for phase-space visibility.
2.  **Momentum Tracking**: $H$ provides a better sense of progress than $V$ alone. A feature with $V=5$ at iteration 10 ($H=15$) is in a very different state than $V=5$ at iteration 2 ($H=7$).
3.  **Actionable Diagnostics**: The diagnostic labels allow the user to quickly identify where the constraint surface is "dense" (requiring more iterations than checks resolved) and where manual intervention is needed.

## Consequences

### Positive
- **Predictability**: Users can estimate completion time by observing the $H$ trend.
- **Spec Compliance**: Full alignment with the v3.0 formal model.

### Negative
- **Table Density**: Adds horizontal width to the `STATUS.md` tables.

## References
- [ADR-S-020: Feature Trajectories as Phase Space Paths](../../../specification/adrs/ADR-S-020-feature-trajectories-phase-space-hamiltonian.md)
