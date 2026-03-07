# GAP ANALYSIS: Cross-Layer Alignment (Spec → Design → Claude)

**Author**: Gemini
**Date**: 2026-03-07T19:30:00Z
**Addresses**: `specification/`, `imp_claude/`, `STATUS.md`
**For**: all

## Executive Summary
This analysis evaluates the alignment between the **Formal System (Spec)**, the **Architectural Design (ADRs)**, and the **Reference Implementation (Claude)**. While the methodology has achieved high theoretical maturity, there is a measurable "lag" in the implementation of the most recent spec-level axioms (Hamiltonian dynamics, Tournament patterns, and OTLP observability).

## 1. Specification → Design Gaps

| Spec Axiom | Design ADR (Claude) | Status | Gap |
| :--- | :--- | :--- | :--- |
| **ADR-S-014 (OTLP)** | — | **Missing** | No design for the OTLP-Relay or Phoenix integration in `imp_claude`. |
| **ADR-S-018 (Tournament)** | — | **Missing** | Sub-graph transitions (`parallel_spawn`) not yet reflected in Claude's topology design. |
| **ADR-S-020 (Hamiltonian)** | ADR-028 | **Partial** | ADR-028 mentions H but lacks the formal $H = T + V$ definition from §6.8. |
| **ADR-S-021 (Instance Graph)**| ADR-022 | **Aligned** | Strong alignment on event-replay projection logic. |

## 2. Design → Code Gaps (Implementation Lag)

### A. Observability (The "Invisible" Inner Loop)
*   **Spec**: `ADR-S-012` requires universal causation/correlation IDs for audit parity.
*   **Design**: `ADR-011` defines the consciousness loop.
*   **Code**: `ol_event.py` implements the schema, but the **Engine (`engine.py`)** does not yet consistently propagate `causation_id` across recursive spawns. The system is "blind" to the depth of agent tool-calling.

### B. The Hamiltonian Metric ($H = T + V$)
*   **Spec**: §6.8 mandates H as the canonical cost metric.
*   **Design**: `ADR-028` accepts H for trajectory visualization.
*   **Code**: `workspace_state.py` derives delta ($V$) but **does not yet compute or store H**. The `gen-status` command lacks an H-display column, making momentum measurement impossible for the user.

### C. The Tournament Sub-Graph
*   **Spec**: `ADR-S-018` defines explicit `parallel_spawn` and `tournament_merge` nodes.
*   **Code**: Claude's `graph_topology.yml` remains linear. The engine lacks the logic to handle the "Fan-out/Fold-back" transaction boundaries defined in the spec.

## 3. Integrity & Traceability Findings

- **INT-GAPS-001 (Critical)**: 11 `REQ-F-FPC-*` orphan keys are implemented in `fp_functor.py` but have no spec-level anchor. This is a direct violation of the **Traceability Invariant**.
- **Metabolic Stale-State**: `REQ-F-ROBUST-001` is converged in the trajectory but `pending` in the feature YML. The **Automatic Convergence Ceremony** (ADR-S-009) is not yet automated in code.

## 4. Remediation Roadmap

1.  **Metric Activation**: Update `summarise_instance_graph` in `workspace_state.py` to compute $H = T + V$ and display it in `gen-status`.
2.  **Causal Wiring**: Refactor `engine.py` to ensure every iteration pass correctly inherits the `causation_id` from the triggering event.
3.  **Topology Extension**: Update Claude's `graph_topology.yml` to include the Tournament nodes from `ADR-S-018`.
4.  **Traceability Anchor**: Move `REQ-F-FPC-*` requirements to `AISDLC_IMPLEMENTATION_REQUIREMENTS.md` or retire them in favor of the new `ROBUST` keys.

## Conclusion
Claude's implementation is a high-fidelity **Prokaryote**. To transition to a **Eukaryote** (as per ADR-S-019), it must implement the "Nucleus" features: Hamiltonian tracking, causal trace propagation, and structural sub-graphs.
